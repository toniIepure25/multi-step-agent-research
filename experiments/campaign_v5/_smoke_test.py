"""One-shot ASAR client smoke test against the remote inference server."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from asar.core.llm import LLMGenerationRequest, LLMMessage, MessageRole


async def test_with_custom_headers():
    """Test using OpenAI SDK with custom headers to bypass Cloudflare."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key="local",
        base_url="https://inference.ccrolabs.com/v1",
        timeout=120.0,
        default_headers={"User-Agent": "ASAR-REE/1.0"},
    )

    for model_id in ["gemma3:27b-it-qat", "llama3.2-vision:11b-instruct-q8_0"]:
        print(f"\n--- Testing {model_id} (custom headers) ---")
        try:
            resp = await client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": "What is 7*8? Reply with only the number."}],
                temperature=0.0,
                max_tokens=16,
            )
            content = resp.choices[0].message.content if resp.choices else "NO CONTENT"
            print(f"  Output: {content.strip()}")
            print(f"  Tokens: in={resp.usage.prompt_tokens} out={resp.usage.completion_tokens}")
            print(f"  PASSED")
        except Exception as exc:
            print(f"  FAILED: {exc}")

    # Also test with httpx directly as fallback diagnostic
    import httpx
    import json
    print("\n--- Direct httpx test ---")
    try:
        async with httpx.AsyncClient(timeout=120.0) as hc:
            r = await hc.post(
                "https://inference.ccrolabs.com/v1/chat/completions",
                json={
                    "model": "gemma3:27b-it-qat",
                    "messages": [{"role": "user", "content": "What is 3+5? Reply with only the number."}],
                    "temperature": 0.0,
                    "max_tokens": 16,
                    "stream": False,
                },
            )
            print(f"  Status: {r.status_code}")
            data = r.json()
            print(f"  Output: {data['choices'][0]['message']['content'].strip()}")
            print(f"  httpx PASSED")
    except Exception as exc:
        print(f"  httpx FAILED: {exc}")


if __name__ == "__main__":
    asyncio.run(test_with_custom_headers())
