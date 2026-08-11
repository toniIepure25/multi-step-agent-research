"""
OpenAI Chat Completions API adapter — works with local models via
Ollama, vLLM, LM Studio, or any OpenAI-compatible server.

Unlike OpenAILLMClient (which uses the Responses API), this adapter
uses the standard /v1/chat/completions endpoint that local inference
servers expose.
"""

from __future__ import annotations

import os
from typing import Any

from asar.core.errors import ConfigurationError, LLMClientError
from asar.core.llm import (
    LLMGenerationRequest,
    LLMGenerationResponse,
    TokenUsage,
)


class ChatCompletionsLLMClient:
    """OpenAI Chat Completions adapter for local/remote models."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY", "local")
        resolved_url = base_url or os.environ.get(
            "ASAR_OPENAI_BASE_URL", "http://localhost:11434/v1",
        )
        headers = default_headers or {"User-Agent": "ASAR-REE/1.0"}

        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ConfigurationError(
                "OpenAI SDK is not installed. Run `uv sync` first.",
            ) from exc

        self._client = AsyncOpenAI(
            api_key=resolved_key,
            base_url=resolved_url,
            timeout=timeout,
            default_headers=headers,
        )

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        messages = []
        for msg in request.messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        try:
            response = await self._client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        except Exception as exc:
            raise LLMClientError(
                "Chat Completions API call failed",
                details={
                    "model": request.model,
                    "error": str(exc),
                },
                retryable=_is_retryable(exc),
            ) from exc

        choice = response.choices[0] if response.choices else None
        if not choice or not choice.message or not choice.message.content:
            raise LLMClientError(
                "Chat Completions returned no content",
                details={"model": request.model},
            )

        usage = response.usage
        return LLMGenerationResponse(
            model=request.model,
            output_text=choice.message.content,
            finish_reason=choice.finish_reason,
            usage=TokenUsage(
                input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            ),
            raw_response=_safe_dump(response),
        )


def _is_retryable(exc: Exception) -> bool:
    exc_str = str(type(exc).__name__).lower()
    return any(k in exc_str for k in ("timeout", "connection", "rate"))


def _safe_dump(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        try:
            return response.model_dump()
        except Exception:
            pass
    return {}
