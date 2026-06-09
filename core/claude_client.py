"""Anthropic SDK wrapper with retry logic and streaming support."""

import os
import time
from typing import Optional, Iterator
import anthropic

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Add it to your .env file."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def call_claude(
    prompt: str,
    system: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    retries: int = 3,
    backoff: float = 2.0,
) -> str:
    """Call Claude and return the full text response."""
    client = get_client()
    for attempt in range(retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            # Log token usage
            usage = message.usage
            print(
                f"  [tokens] input={usage.input_tokens} "
                f"output={usage.output_tokens}"
            )
            return message.content[0].text
        except anthropic.RateLimitError:
            if attempt < retries - 1:
                wait = backoff ** attempt
                print(f"  Rate limited — retrying in {wait:.0f}s...")
                time.sleep(wait)
            else:
                raise
        except anthropic.APIStatusError as e:
            raise RuntimeError(f"Anthropic API error: {e.status_code} {e.message}") from e


def stream_claude(
    prompt: str,
    system: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
) -> Iterator[str]:
    """Yield text chunks from a streaming Claude response."""
    client = get_client()
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text
