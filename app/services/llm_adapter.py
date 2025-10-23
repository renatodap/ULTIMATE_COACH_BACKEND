"""
LLM Adapter Pattern - Unified interface for multiple LLM providers.

Supports:
- OpenRouter (DeepSeek v3.1 :exacto) - Default, 95% cost savings
- Anthropic Claude 3.5 Sonnet - Fallback option

Architecture:
- Abstract base class: LLMAdapter
- Concrete implementations: OpenRouterAdapter, AnthropicAdapter
- Automatic tool format conversion
- Provider-specific cost tracking
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import structlog

logger = structlog.get_logger()


class LLMAdapter(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int,
        system_prompt: Optional[str] = None
    ) -> Any:
        """Create a completion with tool calling support."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name for database storage."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name for tracking."""
        pass

    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD based on provider pricing."""
        pass


class OpenRouterAdapter(LLMAdapter):
    """
    OpenRouter adapter using OpenAI SDK format.

    Default model: DeepSeek v3.1 Terminus :exacto
    - 95% cheaper than Claude ($0.14/$0.28 vs $3/$15 per 1M tokens)
    - Precision routing for tool calling
    - High rate limits
    """

    def __init__(self, api_key: str, model: str = "deepseek/deepseek-v3.1-terminus:exacto"):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://sharpened.app",
                "X-Title": "SHARPENED Ultimate Coach"
            }
        )
        logger.info(
            "llm_adapter_initialized",
            provider="openrouter",
            model=model,
            cost_savings="95% vs Claude"
        )

    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int,
        system_prompt: Optional[str] = None
    ) -> Any:
        """Create completion using OpenAI format."""

        # OpenAI format: system prompt goes as first message
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        openai_messages.extend(messages)

        # Convert tools to OpenAI format if needed
        openai_tools = self._convert_tools_to_openai_format(tools)

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=openai_messages,
            tools=openai_tools
        )

        return response

    def _convert_tools_to_openai_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert Anthropic tool format to OpenAI format.

        Anthropic: {"name": "...", "description": "...", "input_schema": {...}}
        OpenAI: {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}
        """
        openai_tools = []
        for tool in tools:
            # Check if already in OpenAI format
            if "type" in tool and tool["type"] == "function":
                openai_tools.append(tool)
            else:
                # Convert from Anthropic format
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("input_schema", {})
                    }
                })
        return openai_tools

    def get_provider_name(self) -> str:
        """Return 'openai' for database compatibility (OpenRouter uses OpenAI SDK format)."""
        return "openai"

    def get_model_name(self) -> str:
        return self.model

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for DeepSeek v3.1 via OpenRouter.

        Pricing:
        - Input: $0.14 per 1M tokens
        - Output: $0.28 per 1M tokens
        """
        input_cost = (input_tokens / 1_000_000) * 0.14
        output_cost = (output_tokens / 1_000_000) * 0.28
        return input_cost + output_cost


class AnthropicAdapter(LLMAdapter):
    """
    Anthropic Claude adapter.

    Default model: Claude 3.5 Sonnet
    - Premium option for critical tasks
    - Best-in-class reasoning
    - Higher cost ($3/$15 per 1M tokens)
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)
        logger.info(
            "llm_adapter_initialized",
            provider="anthropic",
            model=model
        )

    async def create_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int,
        system_prompt: Optional[str] = None
    ) -> Any:
        """Create completion using Anthropic format."""

        # Anthropic format: system prompt is separate parameter
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=messages,
            tools=tools  # Anthropic tools are already in correct format
        )

        return response

    def get_provider_name(self) -> str:
        return "anthropic"

    def get_model_name(self) -> str:
        return self.model

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for Claude 3.5 Sonnet.

        Pricing:
        - Input: $3.00 per 1M tokens
        - Output: $15.00 per 1M tokens
        """
        input_cost = (input_tokens / 1_000_000) * 3.00
        output_cost = (output_tokens / 1_000_000) * 15.00
        return input_cost + output_cost


def create_llm_adapter(provider: str, **kwargs) -> LLMAdapter:
    """
    Factory function to create LLM adapter.

    Args:
        provider: "openrouter" or "anthropic"
        **kwargs: Provider-specific arguments (api_key, model, etc.)

    Returns:
        LLMAdapter instance

    Example:
        adapter = create_llm_adapter("openrouter", api_key=settings.OPENROUTER_API_KEY)
    """
    if provider == "openrouter":
        return OpenRouterAdapter(**kwargs)
    elif provider == "anthropic":
        return AnthropicAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
