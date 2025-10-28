"""
System Prompt Generator Service

Generates personalized coaching system prompts via Claude meta-prompts.
This is the SECRET WEAPON - creates unique coaching personas for each user.

Architecture:
1. Initial generation: Uses conversational profile from consultation AI
2. Weekly updates: Incorporates behavioral data (adherence, logging, patterns)
3. Version tracking: Enables A/B testing of prompt variants
4. Meta-prompt engineering: Transforms user data into structured system prompts

Example Generated Prompt:
    "You're coaching a 22-year-old male CS student who plays tennis daily
    and is training for a half marathon on Nov 5. His core challenge is
    diet-switching - he's tried keto (lasted 2 weeks), IF (3 days), paleo
    (1 week). He forgets his long-term goals when stressed about performance.

    COMMITTED APPROACH (LOCKED FOR 8 WEEKS):
    - Start: Oct 26, 2025
    - Daily: 2,600-2,800 calories, 200-230g protein, 40g+ fiber
    - Carbs around training (pre-run, post-workout)

    BEHAVIORAL TRIGGERS:
    - When he mentions wanting to try keto/IF/low-carb:
      '⚠️ DIET-SWITCH ALERT ⚠️ You're X days into 8-week commitment.
       You've tried switching before - it lasted 2 weeks then you quit.
       Adherence predicts success, not diet type. Stay the course.'

    - When he mentions performance anxiety:
      'Your training is progressing well. The half marathon is about
       consistency, not perfect performance. Trust the process.'"

Why This Works:
- Specificity: Not "fitness coach" but "coach for THIS person's exact situation"
- Behavioral triggers: Pre-written responses for known failure patterns
- Accountability: Locks them into ONE approach (prevents diet-switching)
- Psychology: Addresses their emotional blockers, not just data
- Evolution: Updates weekly as behavior changes

Cost: $0.05 per generation (one-time + weekly updates)
"""

import structlog
from typing import Dict, Any, Optional
from datetime import datetime, date
from anthropic import AsyncAnthropic

from app.config import settings

logger = structlog.get_logger()


class SystemPromptGenerator:
    """
    Generate personalized coaching system prompts via Claude meta-prompts.

    The meta-prompt transforms user data into structured coaching personas.
    Each user gets a unique 500-800 word system prompt that:
    - Defines their coach's core directive
    - Locks them into ONE committed approach
    - Pre-writes responses for their behavioral triggers
    - Matches their personality/tone preferences
    - Evolves weekly based on actual behavior
    """

    def __init__(self, anthropic_client: AsyncAnthropic):
        """
        Initialize with Anthropic client.

        Args:
            anthropic_client: AsyncAnthropic client for Claude API
        """
        self.anthropic = anthropic_client
        self.model = "claude-3-5-sonnet-20241022"  # Production model

        logger.info("system_prompt_generator_initialized", model=self.model)

    async def generate_initial_prompt(
        self,
        conversational_profile: str,
        onboarding_data: Dict[str, Any],
        user_goals: Dict[str, Any]
    ) -> str:
        """
        Generate initial system prompt from consultation AI output.

        Called after user completes conversational onboarding.
        Uses meta-prompt to transform 200-word profile into 500-800 word system prompt.

        Args:
            conversational_profile: 200-word natural language profile from consultation AI
                Example: "User is 22-year-old CS student, plays tennis daily,
                         training for half marathon. Main issue: cycles between diets
                         (keto, IF, paleo), never sticks >2 weeks. Forgets long-term
                         goals when stressed. Performance anxiety around race."

            onboarding_data: Basic info from minimal signup
                {
                    "age": 22,
                    "biological_sex": "male",
                    "height_cm": 178,
                    "current_weight_kg": 82,
                    "goal_weight_kg": 75,
                    "activity_level": "very_active",
                    "primary_goal": "lose_weight"
                }

            user_goals: Calculated targets
                {
                    "daily_calories": 2600,
                    "protein_g": 200,
                    "carbs_g": 260,
                    "fat_g": 70,
                    "fiber_g": 40
                }

        Returns:
            Complete 500-800 word personalized system prompt

        Example Output:
            "# ACCOUNTABILITY COACH - WEIGHT LOSS & PERFORMANCE SYSTEM

            ## USER PROFILE
            You're coaching a 22-year-old male CS student (178cm, 82kg → 75kg).
            He plays tennis daily and is training for a half marathon on Nov 5.
            Core challenge: Diet-switching. He's tried keto (2 weeks), IF (3 days),
            paleo (1 week) - never sticks to anything. Forgets long-term goals
            when stressed about race performance.

            ## COMMITTED APPROACH (LOCKED FOR 8 WEEKS)
            Start Date: October 26, 2025
            Daily Targets: 2,600-2,800 calories, 200-230g protein, 40g+ fiber
            Meal Structure: Carbs around training (pre-run breakfast, post-workout)

            ## CORE DIRECTIVE
            Your PRIMARY function: Prevent diet-switching. Keep him on THIS plan
            for 8 full weeks. Research shows adherence predicts success, not diet type.

            ## BEHAVIORAL TRIGGERS
            When user mentions wanting to try keto/IF/low-carb:
            '⚠️ DIET-SWITCH ALERT ⚠️ You're X days into 8-week commitment.
             You've tried switching before - it lasted 2 weeks then you quit.
             Adherence predicts success, not diet type. Stay the course.'

            When user mentions performance anxiety:
            'Your training is progressing. The half marathon is about consistency,
             not perfect performance. You're hitting your targets. Trust it.'

            ## ACCOUNTABILITY PROTOCOL
            - Daily: Check weight, meals, training
            - Weekly: Review adherence rate (goal: 5+/7 days in target)
            - Feedback: Direct, no-BS. Call out rationalizations immediately.

            ## TONE
            Direct, honest friend who cares more about results than feelings.
            Interrupt BS rationalizations. Use data + research citations.

            ## PROHIBITED RESPONSES
            - Never say \"it's okay\" or \"don't be hard on yourself\"
            - Never suggest switching diets before 8 weeks ends
            - Never validate approach-switching (his failure pattern)

            ## SUCCESS METRICS
            - 8 weeks on same approach (no diet switches)
            - 75kg by Dec 21 (1kg/week average)
            - Half marathon completed Nov 5 (performance maintained)

            Remember: He has 7kg to lose in 8 weeks while training. This is doable
            if he STAYS THE COURSE. Diet-switching is his enemy, not any specific diet."
        """

        logger.info(
            "generating_initial_system_prompt",
            profile_length=len(conversational_profile),
            has_onboarding=bool(onboarding_data),
            has_goals=bool(user_goals)
        )

        # Build meta-prompt
        meta_prompt = self._build_initial_meta_prompt(
            conversational_profile,
            onboarding_data,
            user_goals
        )

        try:
            # Call Claude to generate system prompt
            response = await self.anthropic.messages.create(
                model=self.model,
                max_tokens=2000,  # 500-800 words = ~1500-2000 tokens
                temperature=0.7,  # Some creativity but mostly consistent
                messages=[{"role": "user", "content": meta_prompt}]
            )

            generated_prompt = response.content[0].text

            logger.info(
                "system_prompt_generated",
                prompt_length=len(generated_prompt),
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                model=response.model
            )

            return generated_prompt

        except Exception as e:
            logger.error(
                "system_prompt_generation_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )

            # Return fallback generic prompt if generation fails
            return self._get_fallback_prompt(onboarding_data, user_goals)

    def _build_initial_meta_prompt(
        self,
        conversational_profile: str,
        onboarding_data: Dict[str, Any],
        user_goals: Dict[str, Any]
    ) -> str:
        """
        Build meta-prompt for initial system prompt generation.

        The meta-prompt is a detailed instruction set for Claude that transforms
        user data into a personalized coaching system prompt.
        """

        today = date.today().strftime("%B %d, %Y")

        # Extract key data
        age = onboarding_data.get("age", "unknown")
        sex = onboarding_data.get("biological_sex", "unknown")
        height_cm = onboarding_data.get("height_cm", 0)
        current_weight = onboarding_data.get("current_weight_kg", 0)
        goal_weight = onboarding_data.get("goal_weight_kg", 0)
        activity_level = onboarding_data.get("activity_level", "moderate")
        primary_goal = onboarding_data.get("primary_goal", "general_fitness")

        daily_cals = user_goals.get("daily_calories", 2000)
        protein_g = user_goals.get("protein_g", 150)
        carbs_g = user_goals.get("carbs_g", 200)
        fat_g = user_goals.get("fat_g", 60)
        fiber_g = user_goals.get("fiber_g", 30)

        return f"""Given this user profile from conversational intake:

{conversational_profile}

And these stats:
- Age: {age}, Sex: {sex}
- Height: {height_cm}cm
- Current weight: {current_weight}kg → Goal: {goal_weight}kg
- Activity level: {activity_level}
- Primary goal: {primary_goal}

Calculated daily targets:
- Calories: {daily_cals} kcal
- Protein: {protein_g}g
- Carbs: {carbs_g}g
- Fat: {fat_g}g
- Fiber: {fiber_g}g

Generate a coaching system prompt (500-800 words) that will be used as Claude's system instructions for this user's AI coach. The prompt should include:

1. **USER PROFILE & CONTEXT** (2-3 sentences)
   - Demographics, current stats, goals
   - Their SPECIFIC challenge (not generic - be precise based on profile)
   - Current life context (training, work stress, competitions, etc.)

2. **COMMITTED APPROACH (LOCKED FOR 8 WEEKS)**
   - Start date: {today}
   - Daily calorie target: {daily_cals}-{int(daily_cals * 1.05)} kcal (5% buffer)
   - Protein target: {protein_g}-{int(protein_g * 1.15)}g
   - Fiber target: {fiber_g}g+ daily
   - Meal structure (based on their schedule/preferences from profile)
   - Specific prohibitions (foods/approaches that triggered past failures)

3. **CORE DIRECTIVE** (1-2 sentences)
   - Primary coaching function based on their SPECIFIC challenge
   - Examples: "prevent diet-switching", "increase meal logging consistency",
     "manage performance anxiety", "overcome decision fatigue"
   - Not generic "help them lose weight" - target their exact failure pattern

4. **BEHAVIORAL TRIGGERS** (3-5 if-then responses)
   - Pre-written responses for their specific patterns from profile
   - Format: "When user [action] → [specific response]"
   - Examples from profile:
     * When they mention wanting to switch diets/try new approach...
     * When they report overeating/binge eating...
     * When they ask about restrictive approaches...
     * When they express frustration/want to quit...
     * When they forget their long-term goal...

5. **ACCOUNTABILITY PROTOCOL**
   - Daily check-in questions (weight, meals, mood, energy)
   - Weekly adherence review (goal: 5+/7 days in calorie target)
   - Feedback style based on their adherence rate:
     * 80%+: Positive reinforcement, maintain course
     * 60-79%: Investigate barriers, adjust if needed
     * <60%: Direct conversation about commitment vs goals

6. **TONE & STYLE** (based on profile)
   - Match their personality: direct/supportive/scientific/tough-love
   - How much hand-holding vs autonomy they need
   - Whether to use research citations or keep it simple
   - Their triggers for feeling shamed/judged (avoid these)

7. **PROHIBITED RESPONSES** (2-3 things)
   - Specific things coach should NEVER say to THIS user
   - Based on what triggers their failures from profile
   - Examples: "Never say 'it's okay to cheat'", "Never suggest switching
     approaches before 8 weeks ends", "Never validate restrictive thinking"

8. **CONFLICT RESOLUTION** (if applicable)
   - If they have conflicting goals (e.g., lose weight fast + perform well),
     which takes priority based on profile?
   - Middleground approach when goals conflict

9. **SUCCESS METRICS** (specific to their timeline)
   - What does success look like for THIS user in 8 weeks?
   - Concrete outcomes, not vague goals
   - Include both physical (weight, performance) and behavioral (adherence, consistency)

Format the output as a clear, structured system prompt that Claude can use directly.
Write in second person ("You're coaching...") as if instructing the AI coach.
Be extremely specific - no generic advice. Every sentence should reference something
from their actual profile or calculated data.

The goal is a prompt so personalized that it could ONLY work for this one user."""

    async def update_prompt_from_behavior(
        self,
        user_id: str,
        current_prompt: str,
        behavioral_data: Dict[str, Any],
        current_profile: Dict[str, Any]
    ) -> str:
        """
        Update system prompt based on observed behavioral data.

        Called weekly by background job if:
        - Adherence < 60% (need to adjust approach)
        - Behavioral patterns changed significantly
        - New life events reported

        Args:
            user_id: User UUID (for logging)
            current_prompt: Existing system prompt
            behavioral_data: Tracked metrics from past 30 days
                {
                    "diet_switches_per_month": 0,  # Good! No switching
                    "meal_logging_streak_days": 42,  # Great streak
                    "avg_days_per_week_in_target": 5.2,  # Strong adherence
                    "most_common_failure_pattern": None,  # No failures
                    "adherence_rate_last_30_days": 0.74  # 74% adherence
                }
            current_profile: Latest profile data (goals may have changed)

        Returns:
            Updated system prompt with adjusted behavioral triggers
        """

        logger.info(
            "updating_system_prompt_from_behavior",
            user_id=user_id,
            adherence_rate=behavioral_data.get("adherence_rate_last_30_days"),
            logging_streak=behavioral_data.get("meal_logging_streak_days"),
            diet_switches=behavioral_data.get("diet_switches_per_month")
        )

        # Build update meta-prompt
        update_meta_prompt = f"""Current system prompt for user:

{current_prompt}

Observed behavioral data from past 30 days:
- Diet approach switches: {behavioral_data.get('diet_switches_per_month', 0)}
- Meal logging streak: {behavioral_data.get('meal_logging_streak_days', 0)} days
- Average days/week in calorie target: {behavioral_data.get('avg_days_per_week_in_target', 0):.1f}/7
- Adherence rate: {behavioral_data.get('adherence_rate_last_30_days', 0):.0%}
- Most common failure pattern: {behavioral_data.get('most_common_failure_pattern', 'None detected')}

Update the BEHAVIORAL TRIGGERS and ACCOUNTABILITY PROTOCOL sections based on:

1. **What's working:**
   - If adherence is high (>70%), reinforce current approach
   - If logging streak is strong, acknowledge consistency
   - If no diet switches, celebrate commitment

2. **What needs adjustment:**
   - If adherence <60%, adjust targets or investigate barriers
   - If logging streak broken, add implementation intentions
   - If diet switches detected, strengthen anti-switching language
   - If new failure patterns emerged, add specific triggers for them

3. **Tone adjustment:**
   - High adherence (>80%): More positive, maintain course
   - Medium adherence (60-80%): Investigative, problem-solving
   - Low adherence (<60%): Direct, recommit or adjust targets

Keep all other sections the same (USER PROFILE, COMMITTED APPROACH, CORE DIRECTIVE, etc.)
Only update the sections that need to adapt to their actual behavior.

Output the complete updated system prompt."""

        try:
            response = await self.anthropic.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": update_meta_prompt}]
            )

            updated_prompt = response.content[0].text

            logger.info(
                "system_prompt_updated",
                user_id=user_id,
                prompt_length=len(updated_prompt),
                tokens_used=response.usage.input_tokens + response.usage.output_tokens
            )

            return updated_prompt

        except Exception as e:
            logger.error(
                "system_prompt_update_failed",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )

            # Return current prompt if update fails
            return current_prompt

    def _get_fallback_prompt(
        self,
        onboarding_data: Dict[str, Any],
        user_goals: Dict[str, Any]
    ) -> str:
        """
        Fallback generic prompt if generation fails.

        Not personalized, but ensures app doesn't break.
        """

        daily_cals = user_goals.get("daily_calories", 2000)
        protein_g = user_goals.get("protein_g", 150)

        return f"""# FITNESS COACH SYSTEM

You're an AI fitness coach helping users achieve their health goals.

## Daily Targets
- Calories: {daily_cals} kcal
- Protein: {protein_g}g

## Approach
- Provide supportive, evidence-based advice
- Track meals and activities
- Give daily feedback on progress
- Encourage consistency over perfection

## Tone
Friendly, motivational, and scientifically accurate."""


# Create singleton instance (will be initialized in main.py with Anthropic client)
_system_prompt_generator: Optional[SystemPromptGenerator] = None


def get_system_prompt_generator() -> SystemPromptGenerator:
    """
    Get singleton System Prompt Generator instance.

    Must be initialized first via init_system_prompt_generator().
    """
    if _system_prompt_generator is None:
        raise RuntimeError(
            "SystemPromptGenerator not initialized. "
            "Call init_system_prompt_generator() first in app startup."
        )
    return _system_prompt_generator


def init_system_prompt_generator(anthropic_client: AsyncAnthropic) -> SystemPromptGenerator:
    """
    Initialize System Prompt Generator singleton.

    Called during app startup in main.py lifespan.
    """
    global _system_prompt_generator
    _system_prompt_generator = SystemPromptGenerator(anthropic_client)
    return _system_prompt_generator
