"""
Stage 3C — Remote LLM Provider.

Synchronous provider for Ollama/OpenAI-compatible inference endpoints.
Uses urllib (stdlib) to avoid corporate proxy issues with third-party HTTP libs.
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CompletionResult:
    """Raw result from a remote LLM completion."""

    model: str
    output_text: str
    finish_reason: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    raw_response: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retries: int = 0


class RemoteLLMProvider:
    """
    Synchronous provider using OpenAI-compatible /v1/chat/completions.

    Designed for controlled scientific experiments — every call is traced.
    """

    def __init__(
        self,
        base_url: str = "https://inference.ccrolabs.com",
        timeout: float = 120.0,
        max_retries: int = 2,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._call_log: list[dict[str, Any]] = []

    @property
    def call_log(self) -> list[dict[str, Any]]:
        return list(self._call_log)

    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> CompletionResult:
        """Execute a chat completion with retry and full tracing."""
        url = f"{self._base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error = None
        for attempt in range(self._max_retries + 1):
            start = time.time()
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "ASAR/1.0",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))

                latency = (time.time() - start) * 1000

                # Parse OpenAI-compatible response
                choices = body.get("choices", [])
                output_text = ""
                finish_reason = ""
                if choices:
                    msg = choices[0].get("message", {})
                    output_text = msg.get("content", "")
                    finish_reason = choices[0].get("finish_reason", "")

                usage = body.get("usage", {})
                result = CompletionResult(
                    model=body.get("model", model),
                    output_text=output_text,
                    finish_reason=finish_reason,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    latency_ms=latency,
                    raw_response=body,
                    retries=attempt,
                )

                self._call_log.append({
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "latency_ms": latency,
                    "tokens": result.total_tokens,
                    "success": True,
                    "attempt": attempt,
                })
                return result

            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
                last_error = str(e)
                latency = (time.time() - start) * 1000
                self._call_log.append({
                    "model": model,
                    "latency_ms": latency,
                    "success": False,
                    "attempt": attempt,
                    "error": last_error,
                })
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)

        return CompletionResult(
            model=model,
            output_text="",
            error=last_error,
            retries=self._max_retries,
        )

    def list_models(self) -> list[dict[str, Any]]:
        """List available models from the API."""
        url = f"{self._base_url}/v1/models"
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ASAR/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("data", [])
