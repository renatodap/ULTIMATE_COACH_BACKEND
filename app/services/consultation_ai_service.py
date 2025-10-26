"""
LLM-Powered Consultation Service

Natural conversation interface that extracts structured data and populates
relational database with precise foreign keys.

Architecture:
- Claude 3.5 Sonnet with tool calling
- Real-time database search and insertion
- Section-specific system prompts
- Conversation history management
"""

import structlog
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from anthropic import Anthropic
from app.config import settings
from app.services.supabase_service import SupabaseService
from app.services.consultation_security import ConsultationSecurity, ConsultationSecurityError

logger = structlog.get_logger()


class ConsultationAIService:
    """
    LLM-powered consultation service that maintains conversation context
    while extracting structured data into the database.
    """

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.anthropic = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.db = SupabaseService()
        self.model = "claude-3-5-sonnet-20241022"
        self.security = ConsultationSecurity()

    # ========================================================================
    # MAIN CONVERSATION HANDLER
    # ========================================================================

    async def process_message(
        self,
        user_id: str,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Process user message in consultation conversation.

        Args:
            user_id: User UUID
            session_id: Consultation session UUID
            message: User's message

        Returns:
            Dict with AI response, extracted items count, and progress
        """
        try:
            # Get session and validate
            session = await self._get_session(session_id)
            if not session:
                raise ValueError(f"Consultation session {session_id} not found")

            # Get conversation history
            history = await self._get_conversation_history(session_id)

            # SECURITY: Validate user message
            try:
                self.security.validate_user_message(
                    message=message,
                    user_id=user_id,
                    session_id=session_id,
                    session_message_count=len(history)
                )
            except ConsultationSecurityError as e:
                logger.warning(f"Security validation failed: {e}")
                return {
                    "success": False,
                    "error": "security_violation",
                    "message": str(e)
                }

            # Get progress summary (what data has been collected so far)
            progress = await self._get_consultation_progress(session_id)

            # Build system prompt for current section
            current_section = session.get("current_section", "training_modalities")
            system_prompt = self._build_system_prompt(current_section, progress)

            # SECURITY: Add safety postamble
            system_prompt += self.security.get_safety_postamble()

            # Prepare messages for Claude
            messages = self._format_messages(history) + [
                {"role": "user", "content": message}
            ]

            # Call Claude with tool access
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=self._get_tools(),
                tool_choice={"type": "auto"}
            )

            # Process tool calls (database operations)
            extracted_items = []
            if response.stop_reason == "tool_use":
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        # SECURITY: Validate tool call before execution
                        try:
                            self.security.validate_tool_call(
                                tool_name=content_block.name,
                                tool_input=content_block.input,
                                current_section=current_section,
                                user_id=user_id
                            )
                        except ConsultationSecurityError as e:
                            logger.error(f"Tool validation failed: {e}")
                            # Log security event
                            self.security.log_security_event(
                                event_type="invalid_tool_call",
                                user_id=user_id,
                                session_id=session_id,
                                details={
                                    "tool_name": content_block.name,
                                    "tool_input": content_block.input,
                                    "error": str(e)
                                }
                            )
                            # Skip this tool call
                            continue

                        tool_result = await self._execute_tool(
                            tool_name=content_block.name,
                            tool_input=content_block.input,
                            user_id=user_id
                        )
                        extracted_items.append(tool_result)

                        # Continue conversation with tool results
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": str(tool_result)
                            }]
                        })

                # Get final response after tool use
                response = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    tools=self._get_tools()
                )

            # Extract text from response
            assistant_message = self._extract_text_from_response(response)

            # SECURITY: Sanitize assistant message
            assistant_message = self.security.validate_assistant_message(assistant_message)

            # Save messages to database
            await self._save_user_message(session_id, user_id, message)
            await self._save_assistant_message(
                session_id,
                user_id,
                assistant_message,
                extracted_items
            )

            # Check if section is complete
            section_complete = self._is_section_complete(current_section, extracted_items)
            if section_complete:
                next_section = self._get_next_section(current_section)
                progress = self._calculate_progress(next_section)
                await self._update_session(
                    session_id,
                    current_section=next_section,
                    progress_percentage=progress
                )
            else:
                progress = session.get("progress_percentage", 0)

            return {
                "success": True,
                "message": assistant_message,
                "extracted_items": len(extracted_items),
                "current_section": current_section,
                "section_complete": section_complete,
                "progress": progress,
                "session_id": session_id
            }

        except Exception as e:
            logger.error(f"Error processing consultation message: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "I'm having trouble processing that. Could you try rephrasing?"
            }

    # ========================================================================
    # SYSTEM PROMPTS (Section-Specific)
    # ========================================================================

    def _build_system_prompt(self, section: str, progress: Optional[Dict[str, Any]] = None) -> str:
        """
        Build dynamic system prompt based on consultation section.
        Includes progress data to prevent duplicate questions.
        """
        base_prompt = """You are an expert fitness coach conducting a consultation with a new client.

CONVERSATION STYLE:
- Warm, encouraging, and knowledgeable
- Ask follow-up questions naturally
- Show expertise (explain WHY you're asking)
- Validate their experience ("Nice numbers!" "That's solid!")
- Be empathetic and understanding
- Don't sound like a form - talk like a real coach

CRITICAL RULES:
1. **Use the database**: When user mentions exercises, foods, or modalities,
   ALWAYS search the database first.
2. **Exact matches**: Insert data using IDs from search results, NOT free text.
3. **Ask for clarification**: If search returns multiple matches or ambiguous
   results, show user the options and let them choose.
4. **Extract as you go**: As soon as you have enough info, call the insert
   tools to save data. Don't wait until end of conversation.
5. **Confirm before saving**: Repeat back what you understood before inserting.
6. **Unit conversion**: Convert imperial to metric automatically (lbs→kg, inches→cm).
7. **NEVER ASK DUPLICATE QUESTIONS**: Check the DATA ALREADY COLLECTED section below.
   If the user has already provided information, DO NOT ask for it again.

"""

        # Add progress summary if available
        if progress:
            import json
            base_prompt += "\n\n--- DATA ALREADY COLLECTED ---\n"
            base_prompt += f"{json.dumps(progress, indent=2)}\n"
            base_prompt += "\nIMPORTANT: Review the data above. Do NOT ask for information that has already been collected.\n"
            base_prompt += "--- END DATA ALREADY COLLECTED ---\n\n"

        section_prompts = {
            "training_modalities": """
CURRENT SECTION: Training Background

YOUR GOAL: Understand what training styles the user follows.

QUESTIONS TO ASK:
- What kind of workouts do you usually do?
- How long have you been training like this?
- What's your experience level?
- Do you follow any specific training program or style?
- Do you do any other types of training?

DATA TO EXTRACT:
- Training modalities (search database first!)
- Years of experience
- Proficiency level (beginner/intermediate/advanced/expert)
- Whether it's their primary modality
- Whether they enjoy it

TOOLS TO USE:
- search_training_modalities(query)
- insert_user_training_modality(...)

EXAMPLE:
User: "I lift weights 4x/week, mainly squats, bench, and deadlifts"
You: [search_training_modalities("powerlifting")]
You: "That sounds like powerlifting-style training! Is that accurate?"
User: "Yeah exactly"
You: "How long have you been training like this?"
User: "About 2 years"
You: [insert_user_training_modality(modality_id="...", years_experience=2, proficiency_level="intermediate")]
You: "Got it - 2 years of powerlifting at intermediate level. Do you do any other training?"
""",

            "exercise_familiarity": """
CURRENT SECTION: Exercise Familiarity

YOUR GOAL: Know which exercises the user can perform.

QUESTIONS TO ASK:
- What exercises are you comfortable with?
- How much weight/reps do you typically use?
- How often do you do these exercises?
- Are there any exercises you can't do or want to avoid?

DATA TO EXTRACT:
- Exercise IDs (search database!)
- Comfort level (1-5 scale)
- Typical performance (weight, reps, duration)
- Frequency (never/rarely/occasionally/regularly/frequently)
- Enjoyment and willingness

TOOLS TO USE:
- search_exercises(query, category, equipment, difficulty)
- insert_user_familiar_exercise(...)
- insert_user_non_negotiable(...) [for excluded exercises]

IMPORTANT:
- When user says "bench" → search "bench press" → likely multiple results
- Show options: "I found Barbell Bench Press, Dumbbell Bench Press, and Incline Bench Press. Which one?"
- Convert weights: 225 lbs = 102 kg
- Extract multiple exercises from one message if mentioned

EXAMPLE:
User: "I squat around 315 for 5 reps, bench 225 for 5"
You: [search_exercises("squat")] [search_exercises("bench press")]
You: "Great numbers! Just to confirm:
• Barbell Back Squat - 143kg × 5 reps
• Barbell Bench Press - 102kg × 5 reps
Is that right?"
User: "Yep"
You: [insert_user_familiar_exercise(exercise_id="squat-uuid", comfort_level=4, typical_weight_kg=143, typical_reps=5)]
You: [insert_user_familiar_exercise(exercise_id="bench-uuid", comfort_level=4, typical_weight_kg=102, typical_reps=5)]
""",

            "training_schedule": """
CURRENT SECTION: Training Schedule

YOUR GOAL: Know when and where the user can train.

QUESTIONS TO ASK:
- Which days can you train?
- What time(s) of day work best?
- How long can you train?
- Where do you train? (home/gym/outdoor)
- Are these times flexible or locked in?

DATA TO EXTRACT:
- Days of week (1=Monday, 7=Sunday)
- Time of day (early_morning/morning/midday/afternoon/evening/night)
- Duration (typical, min, max in minutes)
- Location type
- Flexibility and preference

TOOLS TO USE:
- insert_user_training_availability(...)
- insert_user_non_negotiable(...) [for rest days]

EXAMPLE:
User: "I train Monday, Wednesday, Friday, Saturday mornings at the gym around 6am, about an hour to 90 minutes. Sundays I rest no matter what."
You: [insert for each day]
You: [insert_user_non_negotiable(constraint_type="rest_days", description="Sundays always rest")]
You: "Perfect - 4 days/week, early mornings at the gym, Sundays off. That's a solid schedule!"
""",

            "meal_timing": """
CURRENT SECTION: Meal Timing & Eating Schedule

YOUR GOAL: Understand when the user eats.

QUESTIONS TO ASK:
- What does a typical day of eating look like?
- What times do you usually eat?
- How big are your meals? (small/medium/large)
- Are any meal times non-negotiable? (family dinners, work schedule)
- Do you eat around your workouts?

DATA TO EXTRACT:
- Meal time IDs (from database: breakfast, lunch, dinner, snacks, pre/post-workout)
- Portion sizes
- Flexibility (how many minutes +/-)
- Non-negotiable meal times

TOOLS TO USE:
- get_meal_times() [to see available options]
- insert_user_preferred_meal_time(...)

EXAMPLE:
User: "I eat breakfast around 7am, lunch at noon, then dinner around 6pm. I have a protein shake after my workouts."
You: [insert for breakfast, lunch, dinner, post-workout]
You: "Got it - 3 main meals plus post-workout shake. How would you describe portion sizes?"
""",

            "typical_foods": """
CURRENT SECTION: Typical Foods & Eating Habits

YOUR GOAL: Know what the user already eats.

QUESTIONS TO ASK:
- What do you typically eat for each meal?
- How often do you eat these foods?
- Roughly how much of each food?
- Are there any foods you can't or won't eat?

DATA TO EXTRACT:
- Food IDs (search database!)
- Frequency (daily/several_times_week/weekly/occasionally)
- Typical quantities (grams or servings)
- Meal timing associations
- Foods to exclude

TOOLS TO USE:
- search_foods(query)
- insert_user_typical_meal_food(...)
- insert_user_non_negotiable(...) [for excluded foods]

IMPORTANT:
- Search foods individually: "chicken" → "chicken breast" or "chicken thigh"?
- Ask for specifics: "rice" → white or brown?
- Extract quantities when mentioned
- Handle allergens and preferences

EXAMPLE:
User: "I usually have oatmeal and eggs for breakfast, chicken and rice for lunch"
You: [search_foods for each]
You: "For chicken - breast or thighs? For rice - white or brown?"
User: "Breast and white rice"
You: [insert_user_typical_meal_food for each with frequencies and meal associations]
""",

            "goals_events": """
CURRENT SECTION: Goals & What Success Looks Like

YOUR GOAL: Understand what the user is working toward and WHY.

CRITICAL: Every user has different goals. Don't assume everyone is training for an event or competition.

QUESTIONS TO ASK (Start broad, probe deeper):

1. **Main Goals** (Start here)
   - "What are your main fitness and health goals right now?"
   - "What would success look like for you 3-6 months from now?"
   - "If you could wave a magic wand, what would change about your health/fitness?"

2. **Why This Matters** (Probe motivation)
   - "Why is this important to you?"
   - "What will achieving this give you?"
   - "How will your life be different when you reach this goal?"

3. **Specific Outcomes** (Get concrete)
   - For weight loss: "What's your target weight? When do you want to reach it?"
   - For muscle gain: "How much muscle? Which areas?"
   - For performance: "What specific improvements? (strength, endurance, speed)"
   - For aesthetic: "What look are you going for? Any reference points?"
   - For health: "What health markers? (energy, sleep, pain reduction, blood work)"

4. **Timeline & Urgency**
   - "Is there any specific deadline or event? Or more of a long-term lifestyle change?"
   - "How quickly do you want to see results?"
   - "What's the priority level (1-5)?"

5. **Current vs Target** (Establish baseline)
   - "Where are you now vs where you want to be?"
   - Extract specific current values and targets

6. **Multiple Goals** (Common!)
   - "Do you have other goals too? Sometimes people want to lose fat AND build muscle, or look better AND perform better"
   - Identify conflicts (e.g., weight loss + strength gain) and priorities

GOAL TYPES TO LISTEN FOR:
- **Weight Loss** - target weight, timeline, why they want to lose
- **Muscle Gain** - how much, where, for what reason
- **Body Recomposition** - lose fat AND build muscle simultaneously
- **Performance** - get stronger, run faster, jump higher
- **Aesthetic** - look leaner, more muscular, more toned
- **Health** - more energy, better sleep, less pain, improve blood work
- **Sport-Specific** - improve at tennis, basketball, powerlifting
- **Event-Based** - race, competition, wedding, vacation, reunion
- **Maintenance** - stay where they are, don't regress
- **General Fitness** - "just feel better" or "be more active"

DATA TO EXTRACT:

For improvement goals (insert_user_improvement_goal):
- goal_type: "strength", "endurance", "skill", "aesthetic", "body_composition", "mobility", "performance", "health"
- target_description: User's words - what they want to achieve
- measurement_metric: "weight_kg", "body_fat_%", "squat_max", "run_time_5k", etc.
- current_value: Where they are now
- target_value: Where they want to be
- target_date: When they want to achieve it (nullable if lifestyle goal)
- priority: 1-5 (how important)

For upcoming events (insert_user_upcoming_event) - ONLY if they mention one:
- event_type_id: Search database first
- event_name: "Half Marathon", "Wedding", "Vacation", "Powerlifting Meet"
- event_date: Actual date
- priority: 1-5

TOOLS TO USE:
- search_event_types(query) - IF they mention an event
- insert_user_upcoming_event(...) - IF they have a specific event
- insert_user_improvement_goal(...) - ALWAYS use this for goals

CONVERSATION STYLE:
- Start open-ended: "What are your main fitness and health goals?"
- Don't assume they have an event - many don't
- Validate all goal types: "Wanting to just feel better and have more energy is a great goal"
- Probe the WHY: "Why is losing 20 lbs important to you?"
- Get specific: "When you say 'get toned', what does that look like?"
- Handle multiple goals: "So you want to lose fat but keep or build muscle - got it"

EXAMPLES:

**Example 1: Weight Loss (No Event)**
AI: "What are your main fitness and health goals right now?"
User: "I want to lose about 20 pounds. I just feel uncomfortable in my body."
AI: "Got it. What would reaching that 20 pounds down look like for you - how would your life be different?"
User: "I'd have more energy, feel more confident, and my clothes would fit better. I'm 210 now, want to get to 190."
AI: [insert_user_improvement_goal(
    goal_type="body_composition",
    target_description="Lose 20 lbs to feel more comfortable, have more energy, and fit clothes better",
    measurement_metric="weight_kg",
    current_value=95.3,  # 210 lbs
    target_value=86.2,   # 190 lbs
    target_date=None,    # No specific deadline
    priority=4
)]
AI: "What's the timeline - any specific deadline or more of a long-term change?"
User: "No deadline, just want to do it sustainably this time."

**Example 2: Performance + Event**
AI: "What are your main fitness and health goals?"
User: "I want to hit a 1500lb total in powerlifting by end of year"
AI: [search_event_types("powerlifting meet")]
AI: "Awesome goal! Is there a specific competition or just hitting that number?"
User: "Yeah, there's a meet on December 15th I'm targeting"
AI: [insert_user_upcoming_event(event_type_id="...", event_name="Powerlifting Meet - 1500lb Total", event_date="2025-12-15", priority=5)]
AI: "What's your current total?"
User: "945 right now - 315 squat, 225 bench, 405 deadlift"
AI: [insert_user_improvement_goal for each lift with current and target values, goal_type="strength"]

**Example 3: General Health (No Numbers)**
AI: "What are your main fitness and health goals?"
User: "Honestly, I just want to feel better. I'm always tired and my back hurts."
AI: "Those are really important goals. Let's break that down - when you say 'feel better', what would that look like day-to-day?"
User: "I'd wake up with energy instead of dragging myself out of bed. My lower back wouldn't hurt when I sit at my desk all day. I'd actually want to do stuff on weekends instead of being exhausted."
AI: [insert_user_improvement_goal(
    goal_type="health",
    target_description="Increase daily energy levels, reduce/eliminate lower back pain from desk work, have energy for weekend activities",
    measurement_metric="subjective_energy_1-10",
    current_value=4,
    target_value=8,
    target_date=None,
    priority=5
)]

**Example 4: Aesthetic + Timeline**
AI: "What are your main fitness and health goals?"
User: "I want to look more muscular. I'm tired of being skinny. I'm going to the beach in July and want to look good shirtless."
AI: "Got it - build muscle, look better shirtless by July. What does 'more muscular' look like for you - any specific body parts or overall?"
User: "Mainly chest, arms, and shoulders. I want to fill out a T-shirt better."
AI: [insert_user_upcoming_event(event_type_id="personal_milestone", event_name="Beach Vacation", event_date="2025-07-15", priority=4)]
AI: [insert_user_improvement_goal(
    goal_type="aesthetic",
    target_description="Build visible muscle in chest, arms, shoulders to fill out T-shirts and look good shirtless",
    measurement_metric="subjective_appearance",
    current_value=None,
    target_value=None,
    target_date="2025-07-15",
    priority=5
)]

**Example 5: Multiple Conflicting Goals**
AI: "What are your main fitness and health goals?"
User: "I want to lose fat and build muscle at the same time. And I'm training for a half marathon in 3 weeks."
AI: "Okay, so you've got three things going on - lose fat, build muscle, and perform well in the half marathon. Those can sometimes conflict. Which is the highest priority right now?"
User: "Definitely the half marathon performance. After that, I want to work on body composition."
AI: [insert_user_upcoming_event for half marathon, priority=5]
AI: [insert_user_improvement_goal for endurance/race performance, priority=5]
AI: [insert_user_improvement_goal for body composition, priority=3, target_date=after race]

CRITICAL SUCCESS FACTORS:
1. Start broad - don't assume event or specific goal type
2. Validate ALL goal types - health, aesthetic, maintenance, "just feel better"
3. Probe the WHY - motivation is key for personalization
4. Get specific on what success looks like FOR THEM
5. Handle multiple goals and identify conflicts
6. Extract current state vs target state
7. Understand timeline without assuming there's a deadline

This section should make the user feel heard and understood, regardless of their goal type.""",

            "challenges": """
CURRENT SECTION: Understanding Your Journey (Psychology & Behavioral Patterns)

YOUR GOAL: Extract the USER'S ACTUAL PROBLEM - not just surface goals.
Most users say "I want to lose weight" but the REAL problems are behavioral patterns that prevent success.

CRITICAL APPROACH:
- Probe for PAST FAILURES and WHY they failed (not just what they tried)
- Identify BEHAVIORAL TRIGGERS and repeated patterns
- Understand PSYCHOLOGICAL BLOCKERS (forgetting goals, all-or-nothing thinking, diet-switching)
- Extract CONFLICTS (performance vs weight loss, social eating vs goals)

QUESTIONS TO PROBE (Ask adaptively based on their responses):

1. **Past Attempts**
   - "Tell me about the last time you tried to lose weight or get in shape"
   - Follow up: "How long did you stick with it? What made you stop?"
   - If they mention diets: "Have you tried other approaches? Why didn't they work for you?"

2. **Behavioral Patterns**
   - "When you're trying to stick to a plan, what usually derails you?"
   - "Do you tend to switch between different diet approaches? (keto, IF, paleo, etc.)"
   - "Do you ever feel like you forget your long-term goals in the moment? When does that happen?"

3. **Relationship with Food**
   - "Do you ever find yourself eating when you're not hungry? What triggers that?"
   - "Are there foods or situations where you feel out of control?"
   - "Do you eat differently when stressed vs relaxed?"

4. **Performance Conflicts** (if they train/compete)
   - "Are you training for any events? How does that affect your nutrition choices?"
   - "Have you ever sacrificed performance to lose weight faster? How did that go?"

5. **Decision Fatigue**
   - "Do you ever feel overwhelmed by all the nutrition information out there?"
   - "Have you tried following multiple diet approaches at once or in quick succession?"

6. **Psychological Blockers**
   - "How do you handle 'bad days' - does one bad meal turn into a bad week?"
   - "What scares you most about starting another nutrition program?"
   - "Do you tend to be all-or-nothing? (perfect adherence or giving up completely)"

CONVERSATION STYLE:
- Start broad: "Before we get into the details, tell me about your fitness journey so far"
- Follow up on specifics: "You mentioned trying keto - how long did that last?"
- Probe causality: "What made you stop?" "Why do you think that happened?"
- Validate their experience: "That's really common with endurance athletes"
- Be empathetic: "That cycle of starting and stopping sounds frustrating"
- Sound like a therapist, not a form

WHAT TO LISTEN FOR (These are GOLD for personalized coaching):
- **Repeated patterns**: "I always...", "I keep trying...", "I can't seem to..."
- **Approach-switching**: Mentions multiple diets (keto, IF, paleo, counting macros)
- **Forgetting goals**: "In the moment I just...", "I know I should but..."
- **All-or-nothing**: "Perfect" or "failed", "on the diet" or "off the diet"
- **External triggers**: Stress, travel, social events, weekends, late nights
- **Performance conflicts**: Wants weight loss but has race/competition coming up
- **Specific examples**: "Last Friday I...", "When I'm at my parents' house..."

DATA TO EXTRACT (Save everything they say):
- difficulty_category: "diet_switching", "emotional_eating", "forgetting_long_term_goals",
  "all_or_nothing_thinking", "performance_conflict", "decision_fatigue", "weekend_overeating"
- description: User's EXACT WORDS with specific examples and context
- severity: 1-5 (how much it impacts their progress)
- frequency: "daily", "several_times_weekly", "weekly", "monthly"
- attempted_solutions: What they've tried before (be specific)
- what_worked: If anything helped (usually nothing or very little)
- what_didnt_work: Why solutions failed (THIS IS CRITICAL - extract the actual reason)
- triggers: Specific situations that cause the problem

TOOLS TO USE:
- insert_user_difficulty(...) - Use RICH, detailed descriptions with examples
- insert_user_non_negotiable(...) - For things that MUST be accommodated

EXAMPLE CONVERSATION:

AI: "Before we dive into specifics, I'd love to understand your fitness journey so far. What have you tried in the past to reach your goals?"

User: "I've always had this problem with weight loss. I play tennis every day and I'm training for a half marathon in 2 weeks, but I can never stick to a diet. I've tried keto but only lasted 2 weeks. Then I tried intermittent fasting for like 3 days. Then paleo for a week. I just keep switching and nothing works."

AI: "That cycle of trying different approaches is really frustrating. Let's dig into that. When you were on keto for those 2 weeks, what made you stop?"

User: "Honestly, my performance suffered big time. I felt sluggish during tennis and my runs were terrible. Plus I was eating a ton of meat and cheese which felt wrong. I think it's true that performance suffers on low-carb."

AI: [insert_user_difficulty(
    category="diet_switching",
    description="Cycles between keto (2 weeks), IF (3 days), paleo (1 week) - never sticks to any approach >2 weeks. Plays tennis daily + training for half marathon in 2 weeks. Keto caused sluggish tennis performance and terrible runs (endurance athlete needs carbs). IF created huge meal habit during eating window. Pattern: tries restrictive diet → performance suffers or creates bad habits → abandons approach → tries new diet.",
    severity=5,
    frequency="monthly",
    attempted_solutions="Keto, intermittent fasting, paleo",
    what_didnt_work="Keto compromised endurance performance (tennis + half marathon training). IF led to eating huge meals during window, pattern persisted after stopping. Paleo unclear why stopped.",
    triggers="Training demands conflict with restrictive diets. Wants both performance and weight loss."
)]

AI: "That makes perfect sense - restricting carbs while training for a half marathon is really tough on performance. And you mentioned intermittent fasting for 3 days - why so short?"

User: "I realized that when I do IF, I end up eating HUGE meals during my eating window because I'm so hungry. Then when I stopped IF, I was still eating huge meals but now all day. It's like I got stuck in that pattern."

AI: [Update difficulty with this detail]

AI: "So it sounds like the diet created a habit that outlasted the diet itself. You also mentioned you 'just keep switching' - why do you think that happens?"

User: "Honestly, sometimes I just forget what I'm trying to do. Like in the moment when I'm eating, I kind of lose track of my long-term goal to get to 180 pounds. I'll just keep eating."

AI: [insert_user_difficulty(
    category="forgetting_long_term_goals",
    description="Loses track of long-term weight goal (180 lbs) in the moment while eating - continues eating past fullness. Happens especially after training when very hungry. Says 'in the moment I kind of forget what I'm trying to do.'",
    severity=4,
    frequency="several_times_weekly",
    triggers="After training sessions, extreme hunger, in-the-moment decisions"
)]

AI: "That 'forgetting in the moment' is super common, especially after hard training when you're really hungry. Here's a question - do you tend to be all-or-nothing with your approach? Like you're either 'on' perfectly or you've 'failed' and given up?"

User: "Oh my god yes. If I have one bad day I feel like I've ruined everything."

AI: [insert_user_difficulty(
    category="all_or_nothing_thinking",
    description="One bad meal/day triggers feeling of 'ruined everything' and giving up on the plan. All-or-nothing mindset - either perfect adherence or complete abandonment.",
    severity=5,
    frequency="weekly"
)]

END EXAMPLE.

This section should feel like a deep conversation about their relationship with fitness and food, not a questionnaire. Extract WHY they failed before, not just WHAT they tried. Focus on behavioral patterns and psychological blockers."""
        }

        return base_prompt + section_prompts.get(section, "")

    # ========================================================================
    # TOOL DEFINITIONS
    # ========================================================================

    def _get_tools(self) -> List[Dict[str, Any]]:
        """
        Tool definitions for Claude to call.
        """
        return [
            # SEARCH TOOLS
            {
                "name": "search_training_modalities",
                "description": "Search training modalities database (bodybuilding, powerlifting, CrossFit, etc.)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search term"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_exercises",
                "description": "Search exercise database by name, category, equipment, or muscle groups",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Exercise name or description"},
                        "category": {"type": "string", "enum": ["compound_strength", "isolation_strength", "cardio_steady_state", "cardio_interval", "bodyweight", "olympic_lift", "plyometric", "functional", "flexibility", "mobility", "sports_specific"]},
                        "equipment": {"type": "array", "items": {"type": "string"}},
                        "difficulty": {"type": "string", "enum": ["beginner", "intermediate", "advanced", "expert"]}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_foods",
                "description": "Search food database by name or brand",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Food name"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_meal_times",
                "description": "Get list of available meal times (breakfast, lunch, dinner, snacks, pre/post-workout)",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "search_event_types",
                "description": "Search event types (races, competitions, milestones, etc.)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Event type search"}
                    },
                    "required": ["query"]
                }
            },

            # INSERT TOOLS
            {
                "name": "insert_user_training_modality",
                "description": "Add training modality to user's profile. ONLY call after confirming modality_id from search.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "modality_id": {"type": "string", "description": "UUID from search_training_modalities"},
                        "is_primary": {"type": "boolean", "description": "Is this the primary modality?"},
                        "proficiency_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced", "expert"]},
                        "years_experience": {"type": "integer", "minimum": 0, "maximum": 50},
                        "enjoys_it": {"type": "boolean"}
                    },
                    "required": ["modality_id", "proficiency_level"]
                }
            },
            {
                "name": "insert_user_familiar_exercise",
                "description": "Add exercise to user's familiar exercises. ONLY call after confirming exercise_id from search.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "exercise_id": {"type": "string", "description": "UUID from search_exercises"},
                        "comfort_level": {"type": "integer", "minimum": 1, "maximum": 5, "description": "1=uncomfortable, 5=mastered"},
                        "typical_weight_kg": {"type": "number", "description": "Convert lbs to kg if needed"},
                        "typical_reps": {"type": "integer"},
                        "typical_duration_minutes": {"type": "integer"},
                        "frequency": {"type": "string", "enum": ["never_done", "rarely", "occasionally", "regularly", "frequently"]},
                        "enjoys_it": {"type": "boolean"}
                    },
                    "required": ["exercise_id", "comfort_level", "frequency"]
                }
            },
            {
                "name": "insert_user_training_availability",
                "description": "Add training time slot to user's schedule",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "day_of_week": {"type": "integer", "minimum": 1, "maximum": 7, "description": "1=Monday, 7=Sunday"},
                        "time_of_day": {"type": "string", "enum": ["early_morning", "morning", "midday", "afternoon", "evening", "night"]},
                        "typical_duration_minutes": {"type": "integer", "minimum": 15, "maximum": 240},
                        "min_duration_minutes": {"type": "integer"},
                        "max_duration_minutes": {"type": "integer"},
                        "location_type": {"type": "string", "enum": ["home", "gym", "outdoor", "office", "flexible"]},
                        "is_flexible": {"type": "boolean"},
                        "is_preferred": {"type": "boolean"}
                    },
                    "required": ["day_of_week", "time_of_day", "typical_duration_minutes", "location_type"]
                }
            },
            {
                "name": "insert_user_preferred_meal_time",
                "description": "Add meal time to user's eating schedule",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "meal_time_id": {"type": "string", "description": "UUID from get_meal_times"},
                        "typical_portion_size": {"type": "string", "enum": ["small", "medium", "large"]},
                        "flexibility_minutes": {"type": "integer", "minimum": 0, "maximum": 180},
                        "is_non_negotiable": {"type": "boolean"}
                    },
                    "required": ["meal_time_id", "typical_portion_size"]
                }
            },
            {
                "name": "insert_user_typical_meal_food",
                "description": "Add food to user's typical meals. ONLY call after confirming food_id from search.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "food_id": {"type": "string", "description": "UUID from search_foods"},
                        "meal_time_id": {"type": "string", "description": "UUID from get_meal_times (optional)"},
                        "frequency": {"type": "string", "enum": ["daily", "several_times_week", "weekly", "occasionally"]},
                        "typical_quantity_grams": {"type": "number"},
                        "enjoys_it": {"type": "boolean"}
                    },
                    "required": ["food_id", "frequency"]
                }
            },
            {
                "name": "insert_user_upcoming_event",
                "description": "Add event/goal to user's timeline",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_type_id": {"type": "string", "description": "UUID from search_event_types (optional)"},
                        "event_name": {"type": "string", "description": "Custom event name"},
                        "event_date": {"type": "string", "format": "date"},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 5, "description": "1=low, 5=critical"},
                        "specific_goals": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["event_name", "priority"]
                }
            },
            {
                "name": "insert_user_improvement_goal",
                "description": "Add improvement goal to user's profile",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "goal_type": {"type": "string", "enum": ["strength", "endurance", "skill", "aesthetic", "body_composition", "mobility", "performance", "health"]},
                        "target_description": {"type": "string"},
                        "exercise_id": {"type": "string", "description": "UUID if goal relates to specific exercise"},
                        "measurement_metric": {"type": "string"},
                        "current_value": {"type": "number"},
                        "target_value": {"type": "number"},
                        "target_date": {"type": "string", "format": "date"},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 5}
                    },
                    "required": ["goal_type", "target_description", "priority"]
                }
            },
            {
                "name": "insert_user_difficulty",
                "description": "Add challenge/difficulty to user's profile",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "difficulty_category": {"type": "string", "enum": ["motivation", "time_management", "injury", "nutrition", "knowledge", "consistency", "energy", "social_support", "equipment_access", "travel", "other"]},
                        "description": {"type": "string"},
                        "severity": {"type": "integer", "minimum": 1, "maximum": 5},
                        "triggers": {"type": "array", "items": {"type": "string"}},
                        "attempted_solutions": {"type": "array", "items": {"type": "string"}},
                        "what_worked": {"type": "string"},
                        "what_didnt_work": {"type": "string"}
                    },
                    "required": ["difficulty_category", "description", "severity"]
                }
            },
            {
                "name": "insert_user_non_negotiable",
                "description": "Add non-negotiable constraint to user's profile",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "constraint_type": {"type": "string", "enum": ["rest_days", "meal_timing", "equipment", "exercises_excluded", "foods_excluded", "time_blocks", "social", "religious", "medical", "other"]},
                        "description": {"type": "string"},
                        "reason": {"type": "string"},
                        "excluded_exercise_ids": {"type": "array", "items": {"type": "string"}},
                        "excluded_food_ids": {"type": "array", "items": {"type": "string"}},
                        "is_permanent": {"type": "boolean"}
                    },
                    "required": ["constraint_type", "description"]
                }
            }
        ]

    # ========================================================================
    # TOOL EXECUTION
    # ========================================================================

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute a tool call - either search database or insert data.
        """
        try:
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

            # SEARCH TOOLS
            if tool_name == "search_training_modalities":
                query = tool_input["query"]
                response = self.db.client.table("training_modalities")\
                    .select("*")\
                    .ilike("name", f"%{query}%")\
                    .execute()

                return {
                    "tool": "search_training_modalities",
                    "results": response.data
                }

            elif tool_name == "search_exercises":
                query = tool_input["query"]
                db_query = self.db.client.table("exercises").select("*")

                # Text search on name
                db_query = db_query.ilike("name", f"%{query}%")

                # Optional filters
                if "category" in tool_input:
                    db_query = db_query.eq("category", tool_input["category"])
                if "difficulty" in tool_input:
                    db_query = db_query.eq("difficulty_level", tool_input["difficulty"])

                response = db_query.limit(10).execute()

                return {
                    "tool": "search_exercises",
                    "results": response.data
                }

            elif tool_name == "search_foods":
                query = tool_input["query"]
                response = self.db.client.table("foods")\
                    .select("*")\
                    .ilike("name", f"%{query}%")\
                    .eq("is_public", True)\
                    .limit(10)\
                    .execute()

                return {
                    "tool": "search_foods",
                    "results": response.data
                }

            elif tool_name == "get_meal_times":
                response = self.db.client.table("meal_times")\
                    .select("*")\
                    .order("display_order")\
                    .execute()

                return {
                    "tool": "get_meal_times",
                    "results": response.data
                }

            elif tool_name == "search_event_types":
                query = tool_input["query"]
                response = self.db.client.table("event_types")\
                    .select("*")\
                    .ilike("name", f"%{query}%")\
                    .execute()

                return {
                    "tool": "search_event_types",
                    "results": response.data
                }

            # INSERT TOOLS
            elif tool_name == "insert_user_training_modality":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_training_modalities")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_training_modality",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            elif tool_name == "insert_user_familiar_exercise":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_familiar_exercises")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_familiar_exercise",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            elif tool_name == "insert_user_training_availability":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_training_availability")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_training_availability",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            elif tool_name == "insert_user_preferred_meal_time":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_preferred_meal_times")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_preferred_meal_time",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            elif tool_name == "insert_user_typical_meal_food":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_typical_meal_foods")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_typical_meal_food",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            elif tool_name == "insert_user_upcoming_event":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_upcoming_events")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_upcoming_event",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            elif tool_name == "insert_user_improvement_goal":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_improvement_goals")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_improvement_goal",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            elif tool_name == "insert_user_difficulty":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_difficulties")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_difficulty",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            elif tool_name == "insert_user_non_negotiable":
                data = {"user_id": user_id, **tool_input}
                response = self.db.client.table("user_non_negotiables")\
                    .insert(data)\
                    .execute()

                return {
                    "tool": "insert_user_non_negotiable",
                    "success": True,
                    "id": response.data[0]["id"]
                }

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}", exc_info=True)
            return {
                "tool": tool_name,
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get consultation session by ID."""
        response = self.db.client.table("consultation_sessions")\
            .select("*")\
            .eq("id", session_id)\
            .single()\
            .execute()
        return response.data if response.data else None

    async def _update_session(
        self,
        session_id: str,
        current_section: Optional[str] = None,
        progress_percentage: Optional[int] = None
    ):
        """Update consultation session progress."""
        updates = {}
        if current_section:
            updates["current_section"] = current_section
        if progress_percentage is not None:
            updates["progress_percentage"] = progress_percentage

        if updates:
            self.db.client.table("consultation_sessions")\
                .update(updates)\
                .eq("id", session_id)\
                .execute()

    async def _get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for session."""
        response = self.db.client.table("consultation_messages")\
            .select("*")\
            .eq("session_id", session_id)\
            .order("created_at")\
            .execute()

        return response.data if response.data else []

    async def _get_consultation_progress(self, session_id: str) -> Dict[str, Any]:
        """Get progress summary showing what data has been collected."""
        try:
            response = self.db.client.rpc("get_consultation_progress", {"p_session_id": session_id}).execute()
            return response.data if response.data else {}
        except Exception as e:
            logger.warning(f"Error getting consultation progress: {e}")
            return {}

    async def _save_user_message(self, session_id: str, user_id: str, message: str):
        """Save user message to database."""
        data = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "user",
            "content": message
        }

        self.db.client.table("consultation_messages")\
            .insert(data)\
            .execute()

        logger.info(f"User message saved (session: {session_id})")

    async def _save_assistant_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        extracted_items: List[Dict[str, Any]]
    ):
        """Save assistant message and extracted data."""
        import json

        data = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "assistant",
            "content": message,
            "extracted_data": json.dumps(extracted_items),
            "ai_model": self.model
        }

        self.db.client.table("consultation_messages")\
            .insert(data)\
            .execute()

        logger.info(f"Assistant message saved with {len(extracted_items)} extracted items")

    def _format_messages(self, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation history for Claude API."""
        messages = []

        for msg in history:
            # Only include user and assistant messages (skip system messages)
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        return messages

    def _extract_text_from_response(self, response) -> str:
        """Extract text content from Claude response."""
        for content_block in response.content:
            if content_block.type == "text":
                return content_block.text
        return ""

    def _is_section_complete(
        self,
        section: str,
        extracted_items: List[Dict[str, Any]]
    ) -> bool:
        """Check if current section has enough data to move on."""
        # Simple heuristic: if we extracted at least one item this message
        return len(extracted_items) > 0

    def _get_next_section(self, current_section: str) -> Optional[str]:
        """Get next consultation section."""
        sections = [
            "training_modalities",
            "exercise_familiarity",
            "training_schedule",
            "meal_timing",
            "typical_foods",
            "goals_events",
            "challenges"
        ]

        try:
            current_index = sections.index(current_section)
            if current_index < len(sections) - 1:
                return sections[current_index + 1]
        except ValueError:
            pass

        return None

    def _calculate_progress(self, section: Optional[str]) -> int:
        """Calculate progress percentage based on current section."""
        sections = [
            "training_modalities",      # 14%
            "exercise_familiarity",     # 28%
            "training_schedule",        # 42%
            "meal_timing",              # 57%
            "typical_foods",            # 71%
            "goals_events",             # 85%
            "challenges"                # 100%
        ]

        if not section:
            return 100

        try:
            index = sections.index(section)
            return int(((index + 1) / len(sections)) * 100)
        except ValueError:
            return 0

    # ========================================================================
    # CONVERSATIONAL PROFILE GENERATION
    # ========================================================================

    async def generate_conversational_profile(
        self,
        session_id: str,
        user_id: str
    ) -> str:
        """
        Generate 200-word conversational profile from consultation messages.

        This profile captures:
        - User's psychology and mindset
        - Past failures and what didn't work
        - Current blockers and challenges
        - Goals and motivations
        - Communication style and preferences

        Args:
            session_id: Consultation session UUID
            user_id: User UUID

        Returns:
            200-word natural language profile string
        """
        try:
            # Fetch all consultation messages
            messages_result = self.db.client.table("consultation_messages")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at")\
                .execute()

            if not messages_result.data or len(messages_result.data) == 0:
                logger.warning(
                    "no_consultation_messages_found",
                    session_id=session_id[:8],
                    user_id=user_id[:8]
                )
                return "User completed consultation but no conversation history available."

            # Build conversation transcript
            transcript = []
            for msg in messages_result.data:
                role = "User" if msg["role"] == "user" else "AI"
                content = msg["content"]
                transcript.append(f"{role}: {content}")

            conversation_text = "\n\n".join(transcript)

            # Meta-prompt to generate profile
            meta_prompt = f"""You are analyzing a fitness consultation conversation to create a brief psychological profile.

CONVERSATION TRANSCRIPT:
{conversation_text}

Generate a 200-word natural language profile that captures:

1. **Psychology & Mindset** (40 words)
   - What's their relationship with fitness/nutrition?
   - All-or-nothing thinker? Perfectionist? Flexible?
   - Stressed? Confident? Anxious?

2. **Past Failures** (40 words)
   - What have they tried before?
   - Why didn't it work?
   - What patterns led to failure?

3. **Current Blockers** (40 words)
   - What's stopping them now?
   - Time? Knowledge? Motivation? Support?
   - Specific obstacles (travel, social eating, etc.)

4. **Goals & Motivation** (40 words)
   - What do they actually want?
   - Why now? What changed?
   - External vs internal motivation?

5. **Communication Style** (40 words)
   - How do they talk about fitness?
   - Need encouragement or tough love?
   - Prefer simple or detailed explanations?

IMPORTANT:
- Write in third person ("They...", "The user...")
- Be specific, not generic
- Focus on psychological insights, not just facts
- Exactly 200 words
- Natural language, not bullet points"""

            # Call Claude to generate profile
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": meta_prompt
                }]
            )

            conversational_profile = response.content[0].text.strip()

            logger.info(
                "conversational_profile_generated",
                session_id=session_id[:8],
                user_id=user_id[:8],
                profile_length=len(conversational_profile.split())
            )

            return conversational_profile

        except Exception as e:
            logger.error(
                "conversational_profile_generation_failed",
                session_id=session_id[:8],
                user_id=user_id[:8],
                error=str(e),
                exc_info=True
            )
            # Return fallback profile
            return "User completed consultation. Profile generation failed - using generic coaching approach."

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def start_consultation(
        self,
        user_id: str,
        consultation_key: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new consultation session.

        NOW FREE: Consultation key is optional. If not provided, consultation
        is free for all users (part of onboarding flow).

        Args:
            user_id: User UUID
            consultation_key: Optional consultation key (for premium/gifted access)
            ip_address: Client IP for tracking
            user_agent: Client browser for tracking

        Returns:
            Dict with session_id and initial message
        """
        try:
            # Create session first
            session_data = {
                "user_id": user_id,
                "current_section": "training_modalities",
                "progress_percentage": 0
            }

            response = self.db.client.table("consultation_sessions")\
                .insert(session_data)\
                .execute()

            session_id = response.data[0]["id"]

            # If consultation key provided, validate and redeem it (optional premium feature)
            if consultation_key:
                key_validation = self.db.client.rpc(
                    "validate_and_redeem_consultation_key",
                    {
                        "p_key_code": consultation_key,
                        "p_user_id": user_id,
                        "p_session_id": session_id,
                        "p_ip_address": ip_address,
                        "p_user_agent": user_agent
                    }
                ).execute()

                key_result = key_validation.data

                # Check if key validation failed
                if not key_result.get("success"):
                    # Delete the session since key was invalid
                    self.db.client.table("consultation_sessions")\
                        .delete()\
                        .eq("id", session_id)\
                        .execute()

                    return {
                        "success": False,
                        "error": key_result.get("error"),
                        "message": key_result.get("message")
                    }

                logger.info("consultation_key_redeemed", user_id=user_id[:8], session_id=session_id[:8])
            else:
                # Free consultation (no key required)
                logger.info("free_consultation_started", user_id=user_id[:8], session_id=session_id[:8])

            # Generate welcome message
            initial_message = """Hey! I'm excited to help you build a personalized training and nutrition plan. 🎯

This consultation will take about 15-20 minutes. I'll ask you questions about your training background, goals, schedule, and eating habits. The more details you give me, the better I can tailor your plan.

Let's start with your training. **What kind of workouts do you usually do?**"""

            await self._save_assistant_message(
                session_id=session_id,
                user_id=user_id,
                message=initial_message,
                extracted_items=[]
            )

            return {
                "success": True,
                "session_id": session_id,
                "message": initial_message,
                "current_section": "training_modalities",
                "progress": 0
            }

        except Exception as e:
            logger.error(f"Error starting consultation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
