# Loading State UX - Smart Context-Aware Feedback

## Overview

The AI coach uses **3-tier loading state management** to provide graceful UX during message processing:

1. **TIER 1**: Fast messages (< 2s) - Simple "typing..." indicator
2. **TIER 2**: Medium messages (2-4s) - Context-aware status after 2s
3. **TIER 3**: Slow messages (> 4s) - Backend ACK + context-aware status

This ensures users ALWAYS know what's happening, without cluttering the UI for fast operations.

---

## The Problem We Solved

### OLD APPROACH (Silent Processing):
```
User: "Log breakfast and give me a workout"
[8 seconds of silence with generic "typing..." spinner]
User: "Is it working? Did it freeze?"
```

**Result**: User anxiety, perceived lag, confusion

### NEW APPROACH (Smart Feedback):
```
User: "Log breakfast and give me a workout"
[Instant: "Let me check." appears]
[Shows: "Calculating nutrition..."]
[3s: Status changes to "Finding exercises..."]
[7s: Full response appears]
```

**Result**: User knows EXACTLY what's happening, feels responsive

---

## Frontend Implementation Guide

### 1. State Management

```typescript
// CoachChat.tsx (or your chat component)
interface LoadingStatus {
  show: boolean;
  message: string;
}

const [loadingStatus, setLoadingStatus] = useState<LoadingStatus>({
  show: false,
  message: "Coach is typing..."
});

const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
```

### 2. Message Sending Flow

```typescript
const sendMessage = async (messageText: string) => {
  setIsWaitingForResponse(true);

  // TIER 1: Show basic loading immediately
  setLoadingStatus({ show: true, message: "Coach is typing..." });

  // TIER 2: After 2s, upgrade to context-aware status
  const contextTimeout = setTimeout(() => {
    setLoadingStatus({
      show: true,
      message: getSmartLoadingMessage(messageText)
    });
  }, 2000);

  try {
    // Send message to backend
    const response = await api.sendMessage({
      message: messageText,
      conversation_id: currentConversationId
    });

    // Clear loading
    clearTimeout(contextTimeout);
    setLoadingStatus({ show: false, message: "" });
    setIsWaitingForResponse(false);

    // Handle response
    if (response.success) {
      // Check if there was a quick ACK first
      const quickAckId = response.context_used?.is_temporary_ack
        ? response.message_id
        : null;

      if (quickAckId) {
        // Backend sent a quick ACK - frontend can choose to show it or skip it
        // Option 1: Show ACK briefly, then replace with final response
        // Option 2: Skip ACK and just show final response (cleaner)
      }

      // Add final response to chat
      addMessageToChat({
        id: response.message_id,
        role: 'assistant',
        content: response.message,
        timestamp: new Date()
      });
    }

  } catch (error) {
    clearTimeout(contextTimeout);
    setLoadingStatus({ show: false, message: "" });
    setIsWaitingForResponse(false);

    // Handle error
    showError("Failed to send message. Please try again.");
  }
};
```

### 3. Smart Loading Message Detection

```typescript
function getSmartLoadingMessage(message: string): string {
  const msg = message.toLowerCase();

  // Nutrition logging
  if (/\b(log|ate|eat|meal|breakfast|lunch|dinner|food)\b/i.test(msg)) {
    return "Calculating nutrition...";
  }

  // Workout requests
  if (/\b(workout|exercise|train|lifting|cardio|plan)\b/i.test(msg)) {
    return "Finding exercises...";
  }

  // Progress/stats
  if (/\b(progress|stats|results|weight|analyze|review)\b/i.test(msg)) {
    return "Checking your progress...";
  }

  // Multi-action (log AND workout)
  if (/\band\b/i.test(msg) && msg.split(' ').length > 10) {
    return "Working on it...";
  }

  // Plan creation
  if (/\b(create|generate|make).*\bplan\b/i.test(msg)) {
    return "Building your plan...";
  }

  // Default
  return "Coach is typing...";
}
```

### 4. Loading Indicator Component

```typescript
// LoadingIndicator.tsx
interface LoadingIndicatorProps {
  message: string;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ message }) => {
  return (
    <div className="flex items-center gap-3 px-4 py-3 text-gray-500 bg-gray-50 rounded-lg">
      {/* Animated dots */}
      <div className="flex gap-1">
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '0ms' }}
        />
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '150ms' }}
        />
        <span
          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: '300ms' }}
        />
      </div>

      {/* Status text */}
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
};
```

### 5. Usage in Chat UI

```typescript
// In your chat component render
return (
  <div className="chat-container">
    {/* Message history */}
    {messages.map(msg => (
      <MessageBubble key={msg.id} message={msg} />
    ))}

    {/* Loading indicator */}
    {loadingStatus.show && (
      <LoadingIndicator message={loadingStatus.message} />
    )}

    {/* Message input */}
    <MessageInput
      onSend={sendMessage}
      disabled={isWaitingForResponse}
    />
  </div>
);
```

---

## Backend Integration

### Quick ACK Detection

Backend sends quick ACKs for slow operations. Frontend can detect this via:

```typescript
// Check if message is a quick ACK
const isQuickAck = (message: any) => {
  return message.context_used?.is_temporary_ack === true;
};

// Handle response
if (response.success) {
  if (isQuickAck(response)) {
    // This is a quick ACK - can show it or skip it
    // Option 1: Show briefly then wait for real response
    addTemporaryMessage(response.message);

    // Option 2: Just update loading status
    setLoadingStatus({
      show: true,
      message: response.message + " (processing...)"
    });
  } else {
    // This is the final response
    addMessageToChat(response);
  }
}
```

### Backend ACK Messages by Language

**English:**
- "Let me check." (logging)
- "Looking it up." (workouts/plans)
- "Calculating." (analysis/progress)
- "Checking." (default)

**Portuguese:**
- "Deixa eu ver." (logging)
- "Procurando." (workouts/plans)
- "Calculando." (analysis/progress)
- "Verificando." (default)

**Spanish:**
- "Déjame ver." (logging)
- "Buscando." (workouts/plans)
- "Calculando." (analysis/progress)
- "Verificando." (default)

---

## User Experience by Scenario

### Scenario 1: Simple Question (< 2s)
```
User: "How much protein?"
[0-1.5s: Shows "Coach is typing..."]
[1.5s: Response appears]
```
**Experience**: Feels instant, clean

---

### Scenario 2: Single Tool Operation (2-4s)
```
User: "Log breakfast - 3 eggs, oatmeal"
[0-2s: "Coach is typing..."]
[2s: "Calculating nutrition..."]
[3.5s: Response appears]
```
**Experience**: User knows nutrition is being calculated

---

### Scenario 3: Multi-Tool Operation (> 4s)
```
User: "Log breakfast and give me a leg workout"
[Backend sends quick ACK immediately]
[0s: "Let me check." appears in chat OR as status]
[0-3s: "Calculating nutrition..."]
[3s: "Finding exercises..."]
[7s: Full response appears]
```
**Experience**: Immediate feedback + context awareness

---

## Design Considerations

### Option A: Show Quick ACK as Message
```
┌─────────────────────────────┐
│ You: Log breakfast and...  │
│ Coach: Let me check.        │ ← Quick ACK (temporary)
│ [Calculating nutrition...]  │ ← Loading status
│                             │
│ [7s later]                  │
│ Coach: Logged. 25g protein, │ ← Final response
│   400 cal. Solid breakfast. │
│                             │
│   Leg workout ready:        │
│   - Leg press: 3x12         │
└─────────────────────────────┘
```
**Pros**: User sees immediate text response
**Cons**: Chat gets cluttered with temporary messages

### Option B: Show Quick ACK as Status Only (RECOMMENDED)
```
┌─────────────────────────────┐
│ You: Log breakfast and...  │
│                             │
│ [Let me check. Processing...]│ ← Quick ACK in status
│ [Calculating nutrition...]  │
│                             │
│ [7s later]                  │
│ Coach: Logged. 25g protein, │ ← Final response
│   400 cal. Solid breakfast. │
│                             │
│   Leg workout ready:        │
│   - Leg press: 3x12         │
└─────────────────────────────┘
```
**Pros**: Cleaner chat, no duplicate messages
**Cons**: None (this is better)

---

## Testing Checklist

### Fast Messages (< 2s)
- [ ] Simple questions show generic "typing..." indicator
- [ ] Indicator disappears when response arrives
- [ ] No context-aware status appears (not needed)

### Medium Messages (2-4s)
- [ ] Initial "typing..." for first 2s
- [ ] Context-aware status appears after 2s
- [ ] Status matches message intent (nutrition, workout, etc.)
- [ ] Indicator disappears when response arrives

### Slow Messages (> 4s)
- [ ] Backend sends quick ACK (check logs)
- [ ] Frontend shows ACK or updated status
- [ ] Context-aware status updates as operations progress
- [ ] Final response replaces ACK cleanly

### Error Handling
- [ ] Loading indicator clears on error
- [ ] Error message shown to user
- [ ] Can retry sending message
- [ ] No stuck loading states

### Languages
- [ ] English: Correct status messages
- [ ] Portuguese: Correct status messages
- [ ] Spanish: Correct status messages

---

## Performance Metrics

**Target latencies:**
- Canned response: 0ms (instant)
- Simple Groq: 500ms (< 2s, no special handling)
- Claude + 1 tool: 2-4s (context-aware status)
- Claude + 2+ tools: 4-8s (quick ACK + status)

**User perception:**
- Without loading states: 4s feels like 8s (anxiety)
- With context-aware states: 8s feels like 4s (informed waiting)

---

## Future Enhancements

### Real-time Status Updates (WebSocket/SSE)
```typescript
// When WebSocket is implemented
socket.on('message_status', (data) => {
  if (data.type === 'quick_ack') {
    setLoadingStatus({ show: true, message: data.content });
  } else if (data.type === 'tool_execution') {
    setLoadingStatus({ show: true, message: `${data.tool_name}...` });
  } else if (data.type === 'final_response') {
    addMessageToChat(data.message);
    setLoadingStatus({ show: false, message: "" });
  }
});
```

### Progressive Response (Streaming)
```typescript
// If streaming is implemented
socket.on('message_chunk', (chunk) => {
  appendToLastMessage(chunk.text);
});
```

---

## Summary

**3-Tier Loading Strategy:**

| Tier | Latency | UX | Backend | Frontend |
|------|---------|-----|---------|----------|
| 1 | < 2s | "Coach is typing..." | No special handling | Basic indicator |
| 2 | 2-4s | Context-aware status | No special handling | Smart status detection |
| 3 | > 4s | Quick ACK + context status | Sends quick ACK | Shows ACK + smart status |

**Result**: Users always know what's happening, without UI clutter for fast operations.

**LOADING STATES ARE NOW: SMART. CONTEXT-AWARE. PERSONALITY-CONSISTENT. ⏳**
