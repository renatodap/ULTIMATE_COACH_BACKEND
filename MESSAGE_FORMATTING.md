# Message Formatting Guide

## How Responses Are Structured

The AI coach uses a **2-stage approach** to deliver concise, human-sounding messages:

1. **Claude generates** the initial response (with structure rules)
2. **Llama post-processes** to enforce brevity and natural language

---

## The Pipeline

```
User Message
    ↓
Claude 3.5 Sonnet (with strict structure prompt)
    ↓
[May still be too long or formal]
    ↓
Groq Llama 3.3 70B (post-processor)
    ↓
[Reformats to: max 4 lines, 60 words, human-sounding]
    ↓
Final Response (mobile-friendly, conversational)
```

**Cost**: Claude ($0.10-0.15) + Llama formatting ($0.0001) = negligible overhead

---

## Structure Rules

### Hard Limits:
- **Max 4 lines** (mobile screen test)
- **Max 60 words total**
- **Line break between sentences** (readability)
- **Sound like texting, not writing**

### Format by Message Type:

#### Questions → [Answer]. [Data]. [Action].
```
User: "How much protein do I need?"

Bad (essay-style):
"That's an excellent question about protein requirements. Protein needs
vary based on several factors including body weight, activity level, and
training goals. Generally speaking, research indicates that 0.8-1g per
pound of bodyweight is optimal for muscle building. However, if you're
just maintaining, you might be fine with less..."

Good (concise + human):
"0.8-1g per lb bodyweight.
For you at 180 lbs = 144-180g daily.
Track it for 3 days and tell me if you're hitting it."
```

#### Logs → Logged. [Metrics]. [Assessment].
```
User: "I ate 3 eggs and oatmeal for breakfast"

Bad:
"Excellent breakfast choice! Your 3 eggs provide approximately 18 grams
of protein, and when combined with oatmeal, you're looking at a balanced
meal with complex carbohydrates for sustained energy. This is a great
foundation for hitting your daily protein goals!"

Good:
"Logged. 25g protein, 45g carbs, 400 cal.
Solid breakfast.
Hit 150g protein today."
```

#### Excuses → [Reality]. [Why]. [Choice].
```
User: "I don't have time to work out"

Bad:
"I understand that time constraints can make it challenging to maintain
a consistent workout routine. However, it's important to prioritize your
health and fitness goals. Perhaps we can explore some time-management
strategies or shorter workout options that might fit better into your
schedule?"

Good:
"'No time' = 'not a priority.'
You have time for Netflix but not 20 min?
If you want results, we need honest priorities.
Can you do 15 min right now?"
```

#### Achievements → [Acknowledge]. [Meaning]. [Continue].
```
User: "I hit my protein goal 7 days in a row!"

Bad:
"Congratulations! That's absolutely fantastic! You're doing an amazing
job staying consistent with your nutrition goals. This kind of dedication
is exactly what leads to long-term success. I'm so proud of your commitment
and consistency. Keep up the great work!"

Good:
"7 days straight hitting protein.
That's real discipline.
Most people can't do that. Respect."
```

---

## Natural Language Guidelines

### ✅ DO (Sound Human):

**Use contractions:**
- "you're" not "you are"
- "that's" not "that is"
- "it's" not "it is"

**Natural flow:**
- "Look," "Real talk," "Your call"
- "Can you do 15 min right now?"
- "Hit 150g protein today."

**Direct address:**
- "You have time" ✅
- "One might have time" ❌

**Casual but not sloppy:**
- "Solid breakfast" ✅
- "Solidly executed meal choice" ❌

### ❌ DON'T (Sound Robotic):

**Avoid formal language:**
- "Generally speaking" ❌
- "Research indicates" ❌
- "Perhaps we can explore" ❌
- "I hope this proves helpful" ❌

**Avoid introductions/outros:**
- "Great question!" ❌
- "Excellent point!" ❌
- "I hope this helps!" ❌
- "Let me explain..." ❌

**Avoid multiple paragraphs:**
```
❌ BAD (essay format):

"First, let's talk about protein requirements.

Protein is essential for muscle building and recovery.
Your needs depend on several factors.

Generally, you'll want to aim for 0.8-1g per pound
of bodyweight. For someone your size, that would be...

I hope this information helps you!"
```

```
✅ GOOD (text format):

"0.8-1g per lb bodyweight.
For you at 180 lbs = 144-180g daily.
Track it for 3 days and tell me if you're hitting it."
```

---

## Formatting Examples

### Example 1: Basic Question

**User**: "What's the best time to eat protein?"

**Before Formatting** (Claude's output):
> "That's a great question about protein timing! While there has been
> a lot of discussion about the 'anabolic window' after workouts, recent
> research has shown that total daily protein intake is more important
> than specific timing. However, spreading your protein intake throughout
> the day (20-30g per meal) is generally optimal for muscle protein
> synthesis. So the short answer is: timing matters less than total
> intake. Eat protein with each meal and you'll be fine!"

**After Formatting** (Llama post-process):
> "Timing doesn't matter much.
> Total daily protein matters more.
> Spread it across meals (20-30g each) and you're good."

**Reduction**: 89 words → 18 words (-80%)

---

### Example 2: Meal Log

**User**: "I had chicken breast with rice and broccoli for lunch"

**Before Formatting**:
> "That sounds like an excellent meal choice! Chicken breast is a
> fantastic source of lean protein, providing about 31g per 100g.
> Combined with rice for complex carbohydrates and broccoli for
> micronutrients and fiber, this is a very well-balanced meal that
> will support your fitness goals nicely. Great work staying on track!"

**After Formatting**:
> "Logged. Chicken + rice + broccoli = balanced meal.
> ~40g protein, 60g carbs.
> Keep it up."

**Reduction**: 62 words → 16 words (-74%)

---

### Example 3: Excuse Handling

**User**: "I'm too tired to work out today"

**Before Formatting**:
> "I understand that fatigue can be a real challenge when it comes to
> maintaining your workout routine. It's important to listen to your body
> and distinguish between true fatigue that requires rest and mental
> fatigue that just needs you to push through. If you're truly exhausted
> or showing signs of overtraining, rest is important. However, if you're
> just feeling mentally tired or unmotivated, often the best thing to do
> is a lighter workout session. The question you need to ask yourself is:
> am I actually overtrained or just making an excuse?"

**After Formatting**:
> "Tired is normal.
> Question: actually overtrained or just lazy?
> If overtrained: rest. If just tired: lighter session.
> Your call."

**Reduction**: 106 words → 22 words (-79%)

---

### Example 4: Achievement Recognition

**User**: "I've logged my meals every day for 2 weeks straight!"

**Before Formatting**:
> "That's absolutely fantastic! Congratulations on maintaining such
> excellent consistency with your meal logging over the past two weeks.
> This kind of dedication to tracking is what truly makes the difference
> in achieving your fitness goals. Consistency is the foundation of all
> progress, and you're demonstrating that perfectly. You should be very
> proud of this accomplishment. Now let's make sure we analyze this data
> and use it to optimize your nutrition plan going forward!"

**After Formatting**:
> "14 days straight logging meals.
> That's real consistency.
> Most people quit after 3 days. Respect."

**Reduction**: 78 words → 15 words (-81%)

---

## Mobile Screen Test

All responses are designed to fit on a mobile screen without scrolling:

```
┌─────────────────────────┐
│ What's up. Let's work.  │ ← Line 1
│                         │
│ 0.8-1g per lb.          │ ← Line 2
│ For you = 144-180g daily│ ← Line 3
│ Track it for 3 days.    │ ← Line 4
│                         │
└─────────────────────────┘
  Mobile screen (iPhone 14)
  ✅ No scrolling needed
```

vs

```
┌─────────────────────────┐
│ That's a great question │
│ about protein requirem- │
│ ents! Protein needs va- │
│ ry based on several fa- │ ← User has to scroll
│ ctors including body... │ ↓
│ ...                     │ ↓
└─────────────────────────┘
  ❌ Too long - user scrolling
```

---

## Language Variations

### English (Direct + Casual):
```
"0.8-1g per lb bodyweight.
For you at 180 lbs = 144-180g daily.
Track it for 3 days and tell me if you're hitting it."
```

### Portuguese (Direto + Casual):
```
"0.8-1g por libra de peso.
Pra você com 180 lbs = 144-180g por dia.
Rastreia por 3 dias e me fala se tá acertando."
```

### Spanish (Directo + Casual):
```
"0.8-1g por libra de peso.
Para ti con 180 lbs = 144-180g diarios.
Rastrealo 3 días y dime si lo estás logrando."
```

**Key**: All languages maintain the same structure and brevity.

---

## Post-Processing Behavior

### When Llama Reformats:
- Original > 70 words OR > 4 lines → **Reformat**
- Original ≤ 70 words AND ≤ 4 lines → **Skip** (already good)

### What Gets Cut:
1. Introductions: "Great question!", "That's interesting!"
2. Conclusions: "I hope this helps!", "Good luck!"
3. Hedging: "Generally speaking", "It's important to note"
4. Repetition: Saying the same thing multiple ways
5. Unnecessary context: Background info user didn't ask for

### What Gets Kept:
1. Key numbers: Protein amounts, calories, macros
2. Direct answers: What they asked for
3. Action items: What to do next
4. Tone: Direct, honest, no BS

---

## Technical Details

### Processing Flow:
```python
# 1. Claude generates with structure rules
claude_response = await claude.generate(...)

# 2. Security validation
is_safe = validate_output(claude_response)

# 3. Post-process formatting
formatted, metadata = await formatter.format_response(
    original_response=claude_response,
    user_message=user_message,
    language=user_language
)

# Metadata includes:
# - reformatted: bool
# - original_words: int
# - formatted_words: int
# - reduction_pct: int
```

### Cost Breakdown:
- Claude response: $0.10-0.15
- Llama formatting: $0.0001 (negligible)
- **Total overhead: ~0.1%**

### Performance:
- Formatting time: 200-400ms (Groq is fast)
- Total response time: 1800-2500ms (mostly Claude)
- **Formatting adds: ~10% latency**

---

## Testing Checklist

Before shipping, test these scenarios:

- [ ] Question response: ≤60 words, ≤4 lines, sounds human
- [ ] Meal log: "Logged. [metrics]. [assessment]."
- [ ] Excuse handling: Direct reality check, not enabling
- [ ] Achievement: Real acknowledgment, not generic praise
- [ ] Long response: Gets reformatted intelligently
- [ ] Short response: Doesn't get reformatted (already good)
- [ ] Multilingual: Works in EN, PT, ES

---

## Monitoring

Track these metrics:

1. **Reformatting rate**: % of responses reformatted
   - Target: 40-60% (Claude sometimes nails it)

2. **Average reduction**: Word count decrease
   - Target: 60-80% reduction when reformatted

3. **User engagement**: Do users prefer short vs long?
   - Track: Response rate, follow-up questions

4. **Language consistency**: Same brevity across all languages
   - Target: ±10 words variance max

---

**MESSAGES ARE NOW: CONCISE. HUMAN. MOBILE-FRIENDLY. 📱**
