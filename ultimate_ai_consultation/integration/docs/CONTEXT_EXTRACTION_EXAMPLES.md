# 🤖 CONTEXT EXTRACTION EXAMPLES
## How AI Extracts Insights from Casual Chat

**Last Updated:** October 14, 2025
**Version:** 1.0

---

## Overview

The Context Extraction system is what makes ULTIMATE COACH truly intelligent. Every message sent to the unified coach is analyzed for:

1. **Informal Activities** - Unstructured exercise ("played tennis", "walked dog")
2. **Life Context** - Events affecting training (stress, travel, injury, energy)
3. **Sentiment** - Mood and motivation scoring (-1.0 to 1.0)

This document shows **real examples** of how the system works.

---

## Informal Activity Extraction

### Example 1: Tennis (Classic Case)

**User Message:**
> "Played tennis today, felt amazing! Went for about an hour."

**AI Extraction Result:**
```json
{
  "activity_detected": true,
  "activity_type": "sports",
  "activity_name": "Tennis",
  "intensity": "moderate",
  "duration_estimate_minutes": 60,
  "should_count_as_workout": true,
  "confidence": 0.95,
  "reasoning": "User explicitly mentioned playing tennis for an hour."
}
```

**What Gets Created:**
- **Activity record** in `activities` table
- **Context log** in `user_context_log` with type `informal_activity`
- Affects next reassessment (reduces gym volume if playing regularly)

---

### Example 2: Dog Walking

**User Message:**
> "I walk my dog for 30 mins every morning before work"

**AI Extraction Result:**
```json
{
  "activity_detected": true,
  "activity_type": "cardio_steady_state",
  "activity_name": "Walking (Dog)",
  "intensity": "low",
  "duration_estimate_minutes": 30,
  "should_count_as_workout": false,
  "confidence": 0.88,
  "reasoning": "Regular daily activity, low intensity. Not a formal workout but good NEAT."
}
```

**What Gets Created:**
- Context log for tracking general activity level
- Does NOT create activity record (too routine, low intensity)
- Used in reassessment to understand user's baseline activity

---

### Example 3: Hiking

**User Message:**
> "Went on a killer hike this weekend. 3 hours, legs are toast!"

**AI Extraction Result:**
```json
{
  "activity_detected": true,
  "activity_type": "cardio_steady_state",
  "activity_name": "Hiking",
  "intensity": "high",
  "duration_estimate_minutes": 180,
  "should_count_as_workout": true,
  "perceived_exertion": 8,
  "confidence": 0.92,
  "reasoning": "Long duration, user reported fatigue ('legs are toast'). Significant workout."
}
```

**What Gets Created:**
- Full activity record (3 hours is significant)
- Context log with high intensity marker
- Next leg day may be adjusted based on recovery needs

---

### Example 4: Pickup Basketball

**User Message:**
> "played pickup basketball for like 2 hours, probably ran more than I have all month lol"

**AI Extraction Result:**
```json
{
  "activity_detected": true,
  "activity_type": "sports",
  "activity_name": "Basketball (Pickup)",
  "intensity": "high",
  "duration_estimate_minutes": 120,
  "should_count_as_workout": true,
  "perceived_exertion": 7,
  "confidence": 0.90,
  "reasoning": "2 hours of interval-style activity. User implies high volume ('ran more than all month')."
}
```

**What Gets Created:**
- Activity record with category `sports`
- Context log noting unusual high activity
- May reduce planned cardio this week

---

### Example 5: Yard Work

**User Message:**
> "Spent 4 hours doing yard work today. Lifting bags of mulch, digging. I'm wiped."

**AI Extraction Result:**
```json
{
  "activity_detected": true,
  "activity_type": "other",
  "activity_name": "Yard Work",
  "intensity": "moderate",
  "duration_estimate_minutes": 240,
  "should_count_as_workout": true,
  "perceived_exertion": 6,
  "confidence": 0.85,
  "reasoning": "Long duration, physical labor with resistance component (lifting bags). User reports fatigue."
}
```

**What Gets Created:**
- Activity record (4 hours is significant physical work)
- Context log noting extra volume
- Reassessment accounts for total weekly volume including this

---

### Example 6: Playing with Kids

**User Message:**
> "Chased the kids around the park for an hour. Does that count as cardio? 😅"

**AI Extraction Result:**
```json
{
  "activity_detected": true,
  "activity_type": "other",
  "activity_name": "Active Play (Kids)",
  "intensity": "low-moderate",
  "duration_estimate_minutes": 60,
  "should_count_as_workout": false,
  "confidence": 0.75,
  "reasoning": "Active but inconsistent intensity. Good NEAT contribution but not structured workout."
}
```

**What Gets Created:**
- Context log (tracks general activity)
- No formal activity record
- Noted for understanding user's baseline activity level

---

## Life Context Extraction

### Example 7: Work Stress

**User Message:**
> "Super stressed at work this week. Huge project due Friday. Haven't been sleeping well."

**AI Extraction Result:**
```json
{
  "context_detected": true,
  "context_type": "stress",
  "severity": "high",
  "affects_training": true,
  "sentiment_score": -0.6,
  "suggested_adaptation": "Reduce training volume by 10-15% this week. Prioritize sleep and recovery. Consider lighter 'deload' sessions.",
  "confidence": 0.92,
  "reasoning": "User reports high stress, poor sleep. Both negatively impact recovery capacity."
}
```

**What Gets Created:**
- Context log with type `stress`, severity `high`
- Affects training flag set to `true`
- Reassessment will see this and potentially adjust plan
- Coach will be more encouraging, less demanding

---

### Example 8: Travel

**User Message:**
> "Traveling for work next week. Will be in hotels Monday-Thursday. No good gym access."

**AI Extraction Result:**
```json
{
  "context_detected": true,
  "context_type": "travel",
  "severity": "moderate",
  "affects_training": true,
  "sentiment_score": 0.0,
  "suggested_adaptation": "Provide bodyweight/hotel room workouts. Reduce expected adherence. Focus on maintenance.",
  "confidence": 0.95,
  "reasoning": "User explicitly states travel with limited gym access. Common training disruption."
}
```

**What Gets Created:**
- Context log with type `travel`
- Coach may proactively suggest hotel room workouts
- Reassessment won't penalize adherence during travel week
- System boosts adherence score to account for circumstances

---

### Example 9: Injury

**User Message:**
> "Tweaked my lower back yesterday. Not terrible but uncomfortable. Worried about squatting."

**AI Extraction Result:**
```json
{
  "context_detected": true,
  "context_type": "injury",
  "severity": "low-moderate",
  "affects_training": true,
  "sentiment_score": -0.4,
  "suggested_adaptation": "Avoid loaded spinal flexion/extension. Skip squats/deadlifts temporarily. Substitute with leg press, split squats. Monitor pain levels.",
  "confidence": 0.88,
  "reasoning": "User reports back injury with functional limitation. Requires exercise modifications."
}
```

**What Gets Created:**
- Context log with type `injury`, severity `moderate`
- Coach will avoid suggesting squats/deadlifts temporarily
- Reassessment accounts for modified training
- System won't penalize for skipping back exercises

---

### Example 10: Low Energy

**User Message:**
> "Just not feeling it today. Really tired. Not sure I can do the full workout."

**AI Extraction Result:**
```json
{
  "context_detected": true,
  "context_type": "energy",
  "severity": "moderate",
  "affects_training": true,
  "sentiment_score": -0.5,
  "suggested_adaptation": "Offer modified 'lite' version of workout. Reduce volume by 30-40%. Encourage showing up even if short session.",
  "confidence": 0.85,
  "reasoning": "User reports low energy and motivation. Better to do something than nothing."
}
```

**What Gets Created:**
- Context log with type `energy`, severity `moderate`
- Coach responds empathetically, offers shortened workout
- Tracks energy patterns over time
- Reassessment may reduce volume if chronic

---

### Example 11: Illness

**User Message:**
> "Been fighting a cold since Tuesday. Finally feeling better today but still not 100%."

**AI Extraction Result:**
```json
{
  "context_detected": true,
  "context_type": "illness",
  "severity": "moderate",
  "affects_training": true,
  "sentiment_score": -0.3,
  "suggested_adaptation": "Return to training gradually. Start with 50% normal volume. Prioritize recovery. No high-intensity work yet.",
  "confidence": 0.90,
  "reasoning": "User was sick, now recovering. Immune system still recovering, need gradual return."
}
```

**What Gets Created:**
- Context log with type `illness`
- Coach recommends light return to training
- Reassessment accounts for missed week
- System won't penalize adherence during illness

---

### Example 12: High Motivation

**User Message:**
> "Feeling amazing lately! PRs in every session. Love this program!"

**AI Extraction Result:**
```json
{
  "context_detected": true,
  "context_type": "motivation",
  "severity": "high",
  "affects_training": false,
  "sentiment_score": 0.9,
  "suggested_adaptation": null,
  "confidence": 0.92,
  "reasoning": "User reports high motivation and progress. Positive signal but no adaptation needed."
}
```

**What Gets Created:**
- Context log with type `motivation`, positive sentiment
- Tracked over time to identify program effectiveness
- Coach reinforces with encouragement
- Used in long-term adherence analysis

---

## Sentiment Scoring Examples

### Very Positive (+0.8 to +1.0)
- "Absolutely crushing it! This is the best I've felt in years!"
- "PR'd on bench today! 225lbs for 3 reps! So pumped!"
- "I love this program. Finally found something that works for me."

### Positive (+0.4 to +0.7)
- "Good workout today. Felt strong."
- "Making progress on my squat form."
- "Had a solid session this morning."

### Neutral (-0.3 to +0.3)
- "Completed today's workout."
- "Did 4 sets of bench press."
- "What time should I train tomorrow?"

### Negative (-0.7 to -0.4)
- "Struggled with the workout today. Not sure why."
- "Feeling discouraged. Scale isn't moving."
- "Tired and sore. This is harder than expected."

### Very Negative (-1.0 to -0.8)
- "I hate this. Want to quit. Nothing is working."
- "Completely overwhelmed. Can't keep up."
- "Failed every set today. Feel terrible about myself."

---

## Edge Cases and How They're Handled

### Edge Case 1: Ambiguous Activity

**User Message:**
> "Went for a quick run this morning"

**Challenge:** "Quick" is vague. Could be 10 mins or 30 mins.

**AI Handling:**
```json
{
  "activity_detected": true,
  "duration_estimate_minutes": 20,
  "confidence": 0.65,
  "reasoning": "'Quick' typically implies 15-25 minutes. Using midpoint estimate."
}
```

---

### Edge Case 2: Planned vs Completed

**User Message:**
> "Planning to hit the gym after work today"

**Challenge:** This is a plan, not a completed activity.

**AI Handling:**
```json
{
  "activity_detected": false,
  "confidence": 0.95,
  "reasoning": "User used future tense ('planning to'). Not a completed activity. No log created."
}
```

---

### Edge Case 3: Past Habitual Activity

**User Message:**
> "I used to play soccer in college but haven't touched a ball in 5 years"

**Challenge:** Past activity, no longer relevant.

**AI Handling:**
```json
{
  "activity_detected": false,
  "confidence": 0.90,
  "reasoning": "Past tense ('used to'). Not current activity. May inform persona detection but no activity log."
}
```

---

### Edge Case 4: Watching Sports

**User Message:**
> "Watched the game last night, crazy finish!"

**Challenge:** Watching ≠ playing.

**AI Handling:**
```json
{
  "activity_detected": false,
  "confidence": 0.98,
  "reasoning": "'Watched' indicates spectating, not participating. No activity."
}
```

---

### Edge Case 5: Sarcasm/Humor

**User Message:**
> "Oh yeah, totally did a 5 hour marathon of lifting the remote control 😂"

**Challenge:** User is joking.

**AI Handling:**
```json
{
  "activity_detected": false,
  "confidence": 0.85,
  "reasoning": "Context suggests sarcasm (emoji, 'remote control'). No serious activity."
}
```

---

## Multi-Extraction in Single Message

### Example 13: Complex Message

**User Message:**
> "Played tennis for 2 hours yesterday and absolutely destroyed my legs. Probably overdid it. Also super stressed about work presentation tomorrow. Might need to skip leg day."

**AI Extractions:**

**Extraction 1 - Informal Activity:**
```json
{
  "activity_type": "sports",
  "activity_name": "Tennis",
  "duration_estimate_minutes": 120,
  "intensity": "high",
  "should_count_as_workout": true
}
```

**Extraction 2 - Physical Fatigue Context:**
```json
{
  "context_type": "energy",
  "severity": "high",
  "affects_training": true,
  "description": "Legs very fatigued from tennis",
  "suggested_adaptation": "Skip or significantly reduce leg day. Allow recovery."
}
```

**Extraction 3 - Stress Context:**
```json
{
  "context_type": "stress",
  "severity": "moderate",
  "affects_training": true,
  "description": "Work presentation stress",
  "sentiment_score": -0.5
}
```

**What Gets Created:**
- 1 activity record (tennis)
- 2 context logs (fatigue, stress)
- Coach will likely agree to skip/modify leg day

---

## Testing Context Extraction

### Manual Testing

```python
from app.services.context_extraction import process_message_for_context
import asyncio

# Test message
message = "Played tennis today, felt amazing!"
user_id = "test-user-123"

# Run extraction
result = asyncio.run(process_message_for_context(
    message=message,
    user_id=user_id,
    db=db_connection
))

print(result)
```

### Expected Output

```json
{
  "informal_activity": {
    "detected": true,
    "activity_id": "uuid-here",
    "activity_name": "Tennis",
    "confidence": 0.95
  },
  "life_context": {
    "detected": false
  },
  "sentiment": {
    "score": 0.8,
    "label": "positive"
  }
}
```

---

## Cost Analysis

**Per Message Processing:**
- Model: Claude 3.5 Haiku
- Average tokens: 500 in + 200 out
- Cost: ~$0.0005 per message

**Per User Per Month:**
- Estimate: 100 messages
- Total: $0.05

**Very affordable for the intelligence gained!**

---

## Improving Extraction Accuracy

### 1. Prompt Engineering
The extraction prompts in `context_extraction.py` can be tuned for better accuracy.

### 2. Fine-Tuning
Train a fine-tuned model on labeled user data for domain-specific extraction.

### 3. User Feedback Loop
Allow users to correct extractions:
- "This activity was actually 45 mins, not 60"
- "I wasn't that stressed, just mentioning it"

### 4. Confidence Thresholds
Only create records above confidence threshold (e.g., 0.7).

---

## Future Enhancements

### 1. Photo Extraction
Extract activities from photos (plate of food, gym selfie).

### 2. Voice Message Processing
Directly process voice messages for activity logging.

### 3. Proactive Suggestions
"I noticed you've been stressed this week. Want me to adjust your plan?"

### 4. Pattern Recognition
"You've played tennis 3x in past 2 weeks. Should I reduce gym leg volume?"

---

## Support

For questions about Context Extraction:
- **Code**: `backend/app/services/context_extraction.py`
- **Tests**: `tests/test_context_extraction.py`
- **Database**: `user_context_log` table

---

**The magic is in the details. Every message teaches the system about you.**
