# Memory Architecture - 3-Tier System

## Overview

The AI coach uses a **3-tier memory system** to intelligently remember conversations:

1. **Tier 1**: Working memory (last 10 messages) - ALWAYS included
2. **Tier 2**: Important context (keyword-matched from 11-50) - AUTOMATIC
3. **Tier 3**: Semantic search (all messages) - TOOL-BASED (coming soon)

This ensures the coach remembers **recent conversation + critical user information** without bloating token budget.

---

## The Problem We Solved

### OLD APPROACH (Dumb Truncation):
```
Conversation has 50 messages
Token budget = 2000 tokens
→ Include last 20 messages (whatever fits)
→ Lose messages 1-30
→ Lose important user info (allergies, injuries, goals)
```

**Example Failure**:
```
Message 10: "I'm allergic to dairy"
...
Message 45 (current): "Give me a meal plan"

OLD SYSTEM:
Context = Messages 26-45 (last 20)
❌ Message 10 LOST
AI suggests dairy → User upset
```

### NEW APPROACH (Smart Retrieval):
```
Conversation has 50 messages
Token budget = 1200 tokens

TIER 1: Include last 10 messages (always)
TIER 2: Scan 11-50 for important keywords
        → Found "allergic to dairy" in message 10
        → Include it!

Context = Message 10 + Messages 36-45
✅ Allergy remembered
AI suggests dairy-free plan → User happy
```

---

## 3-Tier Breakdown

### **TIER 1: Working Memory** (Always Included)

**What**: Last 10 messages
**When**: ALWAYS
**Why**: Recent conversation context
**Cost**: ~400-500 tokens

```python
# Always retrieves last 10 messages
tier1 = get_messages(order="desc", limit=10)
```

**Example**:
```
Messages 41-50 in conversation
→ Tier 1 provides messages 41-50
→ AI remembers immediate context
```

---

### **TIER 2: Important Context** (Keyword-Triggered)

**What**: Messages 11-50 that contain important keywords
**When**: If current message has important keywords
**Why**: Catch critical user info (allergies, injuries, goals)
**Cost**: ~200-400 tokens (only relevant messages)

**Important Keywords**:
```python
# Medical/Health
allergy, allergic, injury, injured, hurt, pain,
doctor, prescribed, condition, disease, diagnosed

# Physical Limitations
can't, cannot, unable, avoid, shouldn't,
bad knee, bad back, bad shoulder

# Dietary Restrictions
vegan, vegetarian, kosher, halal, gluten,
lactose, intolerance, sensitivity

# Goals (Personalization)
goal, target, want to, trying to, aiming,
objective, plan to

# Strong Preferences
hate, love, favorite, prefer, always, never

# Life Context
pregnant, breastfeeding, work schedule,
shift work, traveling
```

**How It Works**:
```python
# 1. Check if current message has important keywords
if "allergy" in current_message or "goal" in current_message:

    # 2. Scan messages 11-50 for same keywords
    important_messages = []
    for msg in messages_11_to_50:
        if has_important_keyword(msg.content):
            important_messages.append(msg)

    # 3. Include them in context
    return tier1_messages + important_messages
```

**Example Scenario 1** (Allergy):
```
Message 15: "I'm allergic to dairy and shellfish"
...
Message 60 (current): "What should I eat for dinner?"

STEP 1: Current message says "eat" → has keyword "goal/food"
STEP 2: Scan 11-50 → Find "allergic" in message 15
STEP 3: Include message 15 in context

Result:
Context = Message 15 + Messages 51-60
AI Response: "Dinner ideas (dairy-free, no shellfish)..."
```

**Example Scenario 2** (Injury):
```
Message 8: "I have a bad knee, can't do squats"
...
Message 45 (current): "Give me a leg workout"

STEP 1: Current message says "leg workout" → has keyword "workout"
STEP 2: Scan 11-50 → Find "bad knee" in message 8
STEP 3: Include message 8 in context

Result:
Context = Message 8 + Messages 36-45
AI Response: "Leg workout (no squats - lunges, leg press, extensions)..."
```

**Example Scenario 3** (Goal):
```
Message 12: "My goal is to lose 20 lbs"
...
Message 50 (current): "How many calories should I eat?"

STEP 1: Current message says "calories" → has keyword "nutrition"
STEP 2: Scan 11-50 → Find "goal" in message 12
STEP 3: Include message 12 in context

Result:
Context = Message 12 + Messages 41-50
AI Response: "For 20 lb loss: 500 cal deficit daily..."
```

---

### **TIER 3: Semantic Search** (Tool-Based - Coming Soon)

**What**: All messages (semantic similarity search)
**When**: AI explicitly calls tool when needed
**Why**: Find anything from history, even without keywords
**Cost**: ~200 tokens (top 3 results)

**NOT IMPLEMENTED YET**

Will look like:
```python
# AI decides it needs context from far back
tool_call = {
    "name": "semantic_search_user_data",
    "input": {"query": "user's past workout preferences"}
}

# Returns top 3 most similar messages from entire history
results = vector_search(query_embedding, limit=3)
```

---

## Token Budget Management

### Total Budget: 1200 tokens

```
┌─────────────────────────────────┐
│ TIER 1: Last 10 messages        │
│ Cost: ~400-500 tokens           │
│ Always included                 │
└─────────────────────────────────┘
            ↓
┌─────────────────────────────────┐
│ TIER 2: Important context       │
│ Cost: ~200-400 tokens           │
│ Only if keywords detected       │
└─────────────────────────────────┘
            ↓
┌─────────────────────────────────┐
│ TIER 3: Semantic search         │
│ Cost: ~200 tokens               │
│ Tool-based (coming soon)        │
└─────────────────────────────────┘
            ↓
    Total: ~1000-1200 tokens
```

**Budget Protection**:
- Tier 1: Always gets priority
- Tier 2: Stops adding if budget exceeded
- Token estimation: `len(content) // 4`

---

## System Flow

### Message Processing:

```python
async def process_message(user_message):
    # 1. Get memory (3-tier)
    memory = await conversation_memory.get_conversation_context(
        conversation_id=conv_id,
        current_message=user_message,
        token_budget=1200
    )

    # 2. Format for Claude
    messages = []

    # Add Tier 2 first (important context at start)
    for msg in memory["important_context"]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add Tier 1 (recent messages)
    for msg in memory["recent_messages"]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current message
    messages.append({"role": "user", "content": user_message})

    # 3. Call Claude with context
    response = await claude.generate(messages=messages)
```

**Key Point**: Important context goes FIRST so Claude sees it early.

---

## Real-World Examples

### Example 1: Allergy Remembered

```
Conversation Timeline:
────────────────────────────────────────────────────

Message 10:
User: "I'm allergic to peanuts and tree nuts"
AI: "Noted. I'll keep that in mind for meal suggestions."

Messages 11-58:
[Various conversation about workouts, macros, etc.]

Message 59:
User: "Give me a high-protein snack list"

MEMORY RETRIEVAL:
─────────────────
Current message: "high-protein snack list"
→ Contains keyword: "protein" (nutrition-related)
→ Trigger Tier 2 scan

Tier 2 Scan (messages 11-58):
→ Found "allergic to peanuts" in message 10
→ Include message 10 in context

Context Sent to Claude:
1. Message 10 (allergy)
2. Messages 50-58 (recent)
3. Message 59 (current)

AI Response:
"High-protein snacks (nut-free):
- Greek yogurt
- Hard-boiled eggs
- Cheese sticks
- Edamame
- Protein bars (check labels - no tree nuts)"

✅ Allergy remembered and respected
```

### Example 2: Injury Accommodation

```
Conversation Timeline:
────────────────────────────────────────────────────

Message 5:
User: "I injured my shoulder last month, can't do overhead press"
AI: "Got it. We'll avoid overhead work while it heals."

Messages 6-45:
[Discussion about diet, cardio, etc.]

Message 46:
User: "Give me an upper body workout"

MEMORY RETRIEVAL:
─────────────────
Current message: "upper body workout"
→ Contains keyword: "workout"
→ Trigger Tier 2 scan

Tier 2 Scan (messages 6-45):
→ Found "injured my shoulder" in message 5
→ Include message 5 in context

Context Sent to Claude:
1. Message 5 (injury)
2. Messages 37-45 (recent)
3. Message 46 (current)

AI Response:
"Upper body workout (no overhead - shoulder injury):
- Bench press
- Rows
- Bicep curls
- Tricep pushdowns
Skip: overhead press, lateral raises"

✅ Injury remembered and accommodated
```

### Example 3: Goal Consistency

```
Conversation Timeline:
────────────────────────────────────────────────────

Message 8:
User: "My goal is to gain 10 lbs of muscle over 3 months"
AI: "Muscle gain goal noted. You'll need calorie surplus + high protein."

Messages 9-60:
[Various workout and diet discussions]

Message 61:
User: "Should I cut calories?"

MEMORY RETRIEVAL:
─────────────────
Current message: "cut calories"
→ Contains keyword: "calories" (nutrition-related)
→ Trigger Tier 2 scan

Tier 2 Scan (messages 9-60):
→ Found "goal is to gain" in message 8
→ Include message 8 in context

Context Sent to Claude:
1. Message 8 (goal)
2. Messages 52-60 (recent)
3. Message 61 (current)

AI Response:
"Cut calories? No.
Your goal is muscle gain (10 lbs in 3 months).
You need a surplus, not a cut.
Stay at +300-500 cal daily."

✅ Goal remembered and enforced
```

---

## Logging Output

When memory retrieval happens, you'll see:

```
[ConversationMemory] 💭 3-tier retrieval for abc12345...
[ConversationMemory] ✅ Tier 1: 10 messages, 420 tokens
[ConversationMemory] 🔍 Current message has important keywords - checking history
[ConversationMemory] ✅ Tier 2: Found 2 important messages, 180 tokens

[UnifiedCoach.claude] 💭 Memory retrieved: Tier1=10, Tier2=2, tokens=600
```

This tells you:
- 10 recent messages retrieved
- 2 important messages found
- Total 600 tokens used

---

## Performance & Cost

### OLD SYSTEM:
- Retrieved: Last 20 messages (whatever fit)
- Tokens: ~800
- Missed: Important info from earlier

### NEW SYSTEM:
- Retrieved: Last 10 + ~2-3 important
- Tokens: ~600
- Includes: Critical user info

**Savings**: 25% fewer tokens, better context!

---

## Future: Tier 3 (Semantic Search)

**Coming soon** as a tool:

```python
# AI can explicitly search history
tool_call = {
    "name": "semantic_search_user_data",
    "input": {
        "query": "user's favorite foods",
        "limit": 3
    }
}

# System searches ALL messages via embeddings
# Returns top 3 most relevant
```

This will enable:
- "What did I say about cardio last month?"
- "Find my workout from 2 weeks ago"
- "What foods do I usually eat?"

---

## Testing Scenarios

### Test 1: Allergy Memory
```
1. User says: "I'm allergic to dairy"
2. Wait 30 messages
3. User says: "Give me a meal plan"
4. ✅ AI should suggest dairy-free meals
```

### Test 2: Injury Memory
```
1. User says: "I have a bad knee"
2. Wait 20 messages
3. User says: "Give me a leg workout"
4. ✅ AI should avoid exercises with knee stress
```

### Test 3: Goal Memory
```
1. User says: "My goal is weight loss"
2. Wait 40 messages
3. User says: "How many calories should I eat?"
4. ✅ AI should suggest deficit for weight loss
```

### Test 4: No False Positives
```
1. User asks: "What's good for breakfast?"
2. ✅ AI should NOT retrieve random old messages
3. ✅ Tier 2 should be empty (no important keywords)
```

---

**MEMORY IS NOW: SMART. AUTOMATIC. CONTEXT-AWARE. 🧠**
