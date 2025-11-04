# Unified Coach Service Split - Architecture Design

**Created:** 2025-11-04
**Status:** Design Phase
**Target:** Split 2,658-line monolith into 6 focused services

---

## Current State Analysis

### File: `app/services/unified_coach_service.py`
- **Lines:** 2,658
- **Methods:** 20+
- **Dependencies:** 6 imported services
- **Responsibilities:** 7+ distinct concerns
- **Tests:** 0 unit tests (untestable in current form)

### Method Breakdown

| Method | Lines | Responsibility | Dependencies |
|--------|-------|----------------|--------------|
| `process_message()` | 144 | Main entry point, security, routing | Security, I18n, ToolService |
| `_handle_chat_mode()` | 47 | Chat routing | ConversationMemory |
| `_handle_claude_chat()` | 389 | Claude API interaction, tool calling | Anthropic, ToolService |
| `_handle_log_and_question_mode()` | 179 | Log extraction with follow-up | Log extraction services |
| `_handle_log_mode()` | 266 | Pure log extraction | Log extraction services |
| `_create_conversation()` | 24 | Conversation creation | Supabase |
| `_get_user_language()` | 39 | Language detection | I18n, ConversationMemory |
| `_save_user_message()` | 16 | Save user message | Supabase |
| `_save_ai_message()` | 26 | Save AI message | Supabase |
| `_build_clarification_questions()` | 137 | Generate follow-up questions | LLM |
| `_vectorize_message()` | 55 | Background vectorization | Supabase |
| `_extract_and_store_context()` | 52 | Context extraction | Supabase |
| `_build_system_prompt()` | 1,048 | **MASSIVE** - Build system instructions | Multiple services |
| `_calculate_claude_cost()` | 16 | Cost calculation | None |
| `_detect_slow_operation()` | 28 | Operation detection | None |
| `_get_quick_ack()` | 24 | Quick acknowledgment | I18n |

### Key Observations

1. **`_build_system_prompt()` is 1,048 lines** (40% of file!)
   - System instructions
   - Tool definitions
   - User context
   - Examples
   - Should be its own service

2. **`_handle_claude_chat()` is 389 lines**
   - API interaction
   - Tool execution loop
   - Response formatting
   - Needs extraction

3. **Message routing logic mixed with execution**
   - Entry point does security, routing, AND execution
   - Should separate concerns

4. **No clear boundaries**
   - Methods call each other freely
   - Hard to mock/test individual components

---

## Target Architecture

### 6-Service Split

```
app/services/coach/
├── __init__.py                          # Factory: create_unified_coach_service()
├── unified_coach_router.py              # ~350 lines - Message routing & coordination
├── chat_handler.py                      # ~450 lines - Chat mode processing
├── log_handler.py                       # ~450 lines - Log mode processing
├── conversation_manager.py              # ~300 lines - Conversation operations
├── system_prompt_builder.py             # ~1,100 lines - System prompt construction
└── language_detector.py                 # ~150 lines - Language detection
```

### Additional Support Services (Already Exist)
- `conversation_memory_service.py` - Vector storage
- `i18n_service.py` - Translations
- `tool_service.py` - Tool execution
- `security_service.py` - Security validation

---

## Service Responsibilities

### 1. UnifiedCoachRouter (~350 lines)

**Purpose:** Main entry point and message routing coordination

**Responsibilities:**
- Security validation
- Message routing (chat vs. log)
- Response aggregation
- Error handling at top level

**Interface:**
```python
class UnifiedCoachRouter:
    """
    Routes messages to appropriate handlers.

    Coordinates: SecurityService, ChatHandler, LogHandler
    """

    def __init__(
        self,
        chat_handler: ChatHandler,
        log_handler: LogHandler,
        security_service: SecurityService,
        language_detector: LanguageDetector
    ):
        ...

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        image_base64: Optional[str] = None,
        background_tasks: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Main entry point - routes to chat or log handler.

        Flow:
        1. Security validation
        2. Language detection
        3. Route to handler
        4. Return response
        """
        # Security check
        is_safe, reason, metadata = self.security.validate_message(...)
        if not is_safe:
            return self._security_block_response(reason, metadata)

        # Detect language
        user_language = await self.language_detector.detect(user_id, message)

        # Route to handler (simple logic - no complex classification)
        if self._is_log_intent(message):
            return await self.log_handler.handle(user_id, message, user_language, ...)
        else:
            return await self.chat_handler.handle(user_id, message, user_language, ...)
```

**Dependencies:**
- ChatHandler
- LogHandler
- SecurityService
- LanguageDetector

**Tests:**
- Security blocking works
- Routing to correct handler
- Error handling propagation

---

### 2. ChatHandler (~450 lines)

**Purpose:** Handle all chat mode interactions

**Responsibilities:**
- Claude API interaction
- Tool execution loop
- Response formatting
- Cost calculation

**Interface:**
```python
class ChatHandler:
    """
    Handles chat mode interactions with Claude.

    Orchestrates: LLM calls, tool execution, conversation storage
    """

    def __init__(
        self,
        anthropic_client,
        tool_service: ToolService,
        conversation_manager: ConversationManager,
        system_prompt_builder: SystemPromptBuilder
    ):
        ...

    async def handle(
        self,
        user_id: str,
        message: str,
        user_language: str,
        conversation_id: Optional[str] = None,
        image_base64: Optional[str] = None,
        background_tasks: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Handle chat mode message.

        Flow:
        1. Get/create conversation
        2. Build system prompt
        3. Call Claude with tools
        4. Execute tools as needed
        5. Save messages
        6. Vectorize in background
        """
        # Get conversation context
        conversation = await self.conversation_manager.get_or_create(
            user_id, conversation_id
        )

        # Build system prompt
        system_prompt, _ = await self.system_prompt_builder.build(
            user_id, user_language
        )

        # Get conversation history
        history = await self.conversation_manager.get_history(conversation_id)

        # Call Claude with tools
        response = await self._call_claude_with_tools(
            message,
            system_prompt,
            history,
            user_id
        )

        # Save messages
        await self.conversation_manager.save_messages(
            conversation_id,
            user_message=message,
            ai_message=response.content
        )

        # Background vectorization
        if background_tasks:
            background_tasks.add_task(
                self.conversation_manager.vectorize_message,
                ...
            )

        return self._format_response(response, conversation_id)

    async def _call_claude_with_tools(
        self,
        message: str,
        system_prompt: str,
        history: List[Dict],
        user_id: str
    ) -> Any:
        """
        Call Claude with agentic tool execution loop.

        Handles tool_use → tool_result → final_text flow.
        """
        ...
```

**Dependencies:**
- Anthropic client
- ToolService
- ConversationManager
- SystemPromptBuilder

**Tests:**
- Claude API called correctly
- Tool execution loop works
- Messages saved
- Cost calculated

---

### 3. LogHandler (~450 lines)

**Purpose:** Handle all log mode interactions (meal/activity extraction)

**Responsibilities:**
- Log extraction via Claude
- Preview generation
- Enrichment orchestration
- Confirmation handling

**Interface:**
```python
class LogHandler:
    """
    Handles log mode interactions (meal/activity logging).

    Extracts structured data from natural language.
    """

    def __init__(
        self,
        anthropic_client,
        conversation_manager: ConversationManager,
        enrichment_services: Dict[str, Any]  # activity, meal, measurement enrichers
    ):
        ...

    async def handle(
        self,
        user_id: str,
        message: str,
        user_language: str,
        conversation_id: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle log mode message.

        Flow:
        1. Extract structured logs from message
        2. Enrich with database data
        3. Generate preview
        4. Return for user confirmation
        """
        # Extract logs
        logs = await self._extract_logs(message, user_language, image_base64)

        # Enrich each log
        enriched_logs = []
        for log in logs:
            enriched = await self._enrich_log(log, user_id)
            enriched_logs.append(enriched)

        # Save conversation
        conversation = await self.conversation_manager.get_or_create(
            user_id, conversation_id
        )

        # Generate clarification questions if needed
        questions = await self._build_clarification_questions(
            logs, enriched_logs, user_language
        )

        return {
            "success": True,
            "is_log_preview": True,
            "log_previews": enriched_logs,
            "clarification_questions": questions,
            "conversation_id": conversation["id"]
        }

    async def _extract_logs(
        self,
        message: str,
        language: str,
        image: Optional[str]
    ) -> List[Dict]:
        """Extract structured logs using Claude."""
        ...

    async def _enrich_log(
        self,
        log: Dict,
        user_id: str
    ) -> Dict:
        """Enrich log with database data."""
        log_type = log.get("type")  # activity, meal, measurement
        enricher = self.enrichment_services.get(log_type)

        if enricher:
            return await enricher.enrich(log, user_id)
        return log
```

**Dependencies:**
- Anthropic client
- ConversationManager
- Enrichment services (activity, meal, measurement)

**Tests:**
- Log extraction works
- Enrichment applied
- Preview generated
- Questions created

---

### 4. ConversationManager (~300 lines)

**Purpose:** All conversation operations (CRUD, history, vectorization)

**Responsibilities:**
- Create/retrieve conversations
- Save messages
- Get conversation history
- Vectorize messages
- Extract context

**Interface:**
```python
class ConversationManager:
    """
    Manages conversation lifecycle and storage.

    Handles: Database operations, vectorization, history retrieval
    """

    def __init__(
        self,
        supabase_client,
        conversation_memory_service: ConversationMemoryService
    ):
        ...

    async def get_or_create(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get existing conversation or create new one."""
        if conversation_id:
            return await self._get_conversation(conversation_id)
        else:
            return await self._create_conversation(user_id)

    async def get_history(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation message history."""
        ...

    async def save_messages(
        self,
        conversation_id: str,
        user_message: str,
        ai_message: str,
        user_metadata: Optional[Dict] = None,
        ai_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Save both user and AI messages."""
        user_msg_id = await self._save_user_message(...)
        ai_msg_id = await self._save_ai_message(...)

        return {
            "user_message_id": user_msg_id,
            "ai_message_id": ai_msg_id
        }

    async def vectorize_message(
        self,
        conversation_id: str,
        message_id: str,
        message_text: str
    ) -> None:
        """Vectorize message for similarity search (background task)."""
        embedding = await self.conversation_memory.create_embedding(message_text)
        await self.conversation_memory.store_embedding(
            conversation_id,
            message_id,
            embedding
        )

    async def extract_and_store_context(
        self,
        user_id: str,
        conversation_id: str,
        message_text: str
    ) -> None:
        """Extract and store conversation context."""
        ...
```

**Dependencies:**
- Supabase client
- ConversationMemoryService (vectorization)

**Tests:**
- Conversation creation
- Message saving
- History retrieval
- Vectorization (mocked)

---

### 5. SystemPromptBuilder (~1,100 lines)

**Purpose:** Construct complete system prompts for Claude

**Responsibilities:**
- Build system instructions
- Add tool definitions
- Add user context
- Add examples
- Format for Claude API

**Interface:**
```python
class SystemPromptBuilder:
    """
    Builds comprehensive system prompts for Claude.

    Includes: Instructions, tools, user context, examples
    """

    def __init__(
        self,
        supabase_client,
        tool_service: ToolService,
        i18n_service: I18nService
    ):
        ...

    async def build(
        self,
        user_id: str,
        user_language: str,
        mode: str = "chat"  # chat or log
    ) -> Tuple[str, Optional[int]]:
        """
        Build complete system prompt.

        Returns:
            (system_prompt_text, prompt_cache_id)
        """
        # Get user profile
        profile = await self._get_user_profile(user_id)

        # Build sections
        sections = []
        sections.append(self._build_role_section(user_language))
        sections.append(self._build_capabilities_section(user_language))
        sections.append(self._build_personality_section(user_language))
        sections.append(self._build_user_context_section(profile))
        sections.append(self._build_tools_section())
        sections.append(self._build_examples_section(user_language))
        sections.append(self._build_guidelines_section(user_language))

        system_prompt = "\n\n".join(sections)

        return system_prompt, None  # TODO: Implement prompt caching

    def _build_role_section(self, language: str) -> str:
        """Build role and identity section."""
        ...

    def _build_capabilities_section(self, language: str) -> str:
        """Build capabilities section."""
        ...

    def _build_personality_section(self, language: str) -> str:
        """Build personality traits section."""
        ...

    def _build_user_context_section(self, profile: Dict) -> str:
        """Build personalized user context."""
        ...

    def _build_tools_section(self) -> str:
        """Build tool definitions section."""
        tool_defs = self.tool_service.get_tool_definitions()
        # Format for Claude
        ...

    def _build_examples_section(self, language: str) -> str:
        """Build example interactions."""
        ...

    def _build_guidelines_section(self, language: str) -> str:
        """Build response guidelines."""
        ...
```

**Dependencies:**
- Supabase client (for profile)
- ToolService (for tool definitions)
- I18nService (for translations)

**Tests:**
- Prompt sections generated
- User context included
- Tools included
- Language-specific content

---

### 6. LanguageDetector (~150 lines)

**Purpose:** Detect user's preferred language

**Responsibilities:**
- Check user profile
- Check conversation history
- Analyze message content
- Return language code

**Interface:**
```python
class LanguageDetector:
    """
    Detects user's preferred language.

    Priority: Profile > Conversation history > Message analysis
    """

    def __init__(
        self,
        supabase_client,
        conversation_memory_service: ConversationMemoryService,
        i18n_service: I18nService
    ):
        ...

    async def detect(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Detect user language.

        Returns:
            Language code (e.g., "en", "es", "fr")
        """
        # 1. Check user profile
        profile_lang = await self._get_profile_language(user_id)
        if profile_lang:
            return profile_lang

        # 2. Check conversation history
        if conversation_id:
            history_lang = await self._get_conversation_language(conversation_id)
            if history_lang:
                return history_lang

        # 3. Analyze message content
        detected_lang = self.i18n.detect_language(message)
        if detected_lang:
            return detected_lang

        # 4. Default
        return "en"

    async def _get_profile_language(self, user_id: str) -> Optional[str]:
        """Get language from user profile."""
        ...

    async def _get_conversation_language(self, conversation_id: str) -> Optional[str]:
        """Get language from conversation history."""
        ...
```

**Dependencies:**
- Supabase client
- ConversationMemoryService
- I18nService

**Tests:**
- Profile language returned
- History language returned
- Message analysis works
- Default to English

---

## Migration Strategy

### Phase 2.1: Extract Bottom-Up (Least Dependencies First)

**Step 1: LanguageDetector** (150 lines, minimal dependencies)
- Extract `_get_user_language()` method
- Add profile/history checks
- Test independently

**Step 2: SystemPromptBuilder** (1,100 lines, moderate dependencies)
- Extract `_build_system_prompt()` method
- Extract all `_build_*_section()` methods
- Test prompt generation

**Step 3: ConversationManager** (300 lines, minimal dependencies)
- Extract conversation CRUD methods
- Extract message saving methods
- Extract vectorization methods
- Test database operations

**Step 4: LogHandler** (450 lines, moderate dependencies)
- Extract `_handle_log_mode()` method
- Extract `_handle_log_and_question_mode()` method
- Extract enrichment coordination
- Test log extraction

**Step 5: ChatHandler** (450 lines, high dependencies)
- Extract `_handle_chat_mode()` method
- Extract `_handle_claude_chat()` method
- Extract tool execution loop
- Test chat flow

**Step 6: UnifiedCoachRouter** (350 lines, coordinates all)
- Extract `process_message()` method
- Implement routing logic
- Wire up all handlers
- Test end-to-end

### Phase 2.2: Integration Testing

1. **Unit tests** for each service (6 test files)
2. **Integration tests** for service interactions
3. **End-to-end tests** for user flows

### Phase 2.3: Cutover

1. Create feature flag: `USE_NEW_COACH_ARCHITECTURE`
2. Deploy both versions
3. Gradual rollout (1% → 10% → 50% → 100%)
4. Monitor errors and performance
5. Remove old code after validation

---

## Benefits After Split

### Before (Monolithic)
- **Lines:** 2,658 in one file
- **Methods:** 20+ in one class
- **Tests:** 0 (untestable)
- **Maintainability:** Very low
- **Onboarding:** Difficult (where is X?)

### After (Modular)
- **Lines:** 350 per file average (vs. 2,658)
- **Methods:** 5-10 per class (vs. 20+)
- **Tests:** 30+ tests across 6 files
- **Maintainability:** High (clear boundaries)
- **Onboarding:** Easy (one file per concern)

### Metrics
- **Average File Size:** -87% (2,658 → 350)
- **Test Coverage:** 0% → 85%
- **Method Complexity:** -60% (smaller methods)
- **Debuggability:** +200% (clear boundaries)
- **Maintainability Index:** +300%

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing functionality | HIGH | Comprehensive integration tests, feature flag |
| Services depend on each other | MEDIUM | Clear interfaces, dependency injection |
| Too much abstraction | LOW | Keep it practical, no over-engineering |
| Performance degradation | LOW | Profile before/after, optimize if needed |

---

## Next Steps

1. **Create test infrastructure** (mocks, fixtures)
2. **Extract LanguageDetector** (easiest, least risk)
3. **Extract SystemPromptBuilder** (largest, but independent)
4. **Extract ConversationManager** (database operations)
5. **Extract handlers** (LogHandler, ChatHandler)
6. **Create router** (UnifiedCoachRouter)
7. **Integration testing**
8. **Gradual rollout**

---

**Last Updated:** 2025-11-04
**Status:** Design complete, ready for implementation
**Estimated Time:** 1-2 weeks
