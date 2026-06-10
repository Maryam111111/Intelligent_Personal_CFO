"""Anthropic SDK wrapper with retry logic and streaming support."""

import os
import time
import logging
from typing import Optional, Iterator
import anthropic

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None


def _mask_token(token: str, visible_chars: int = 8) -> str:
    """Mask API token for safe logging."""
    if not token or len(token) <= visible_chars:
        return "***"
    return token[:visible_chars] + "*" * (len(token) - visible_chars)


def get_client() -> anthropic.Anthropic:
    """Get or create Anthropic client singleton."""
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Add it to your .env file. "
                "Get your key from https://console.anthropic.com/"
            )
        _client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"Anthropic client initialized with key {_mask_token(api_key)}")
    return _client


def call_claude(
    prompt: str,
    system: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    retries: int = 3,
    backoff: float = 2.0,
) -> str:
    """
    Call Claude and return the full text response.
    
    Args:
        prompt: User message/question
        system: System prompt/instructions
        model: Claude model identifier
        max_tokens: Maximum tokens in response
        retries: Number of retry attempts on rate limit
        backoff: Exponential backoff multiplier
    
    Returns:
        Claude's text response
        
    Raises:
        EnvironmentError: If API key not configured
        RuntimeError: If API returns an error
    """
    client = get_client()
    
    for attempt in range(retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            # Log token usage (safe to log, doesn't contain sensitive data)
            usage = message.usage
            logger.debug(
                f"API call successful: input={usage.input_tokens} tokens, "
                f"output={usage.output_tokens} tokens"
            )
            return message.content[0].text
            
        except anthropic.RateLimitError as e:
            if attempt < retries - 1:
                wait = backoff ** attempt
                logger.warning(
                    f"Rate limited on attempt {attempt + 1}/{retries}. "
                    f"Retrying in {wait:.0f}s..."
                )
                time.sleep(wait)
            else:
                logger.error("Rate limited after all retries")
                raise RuntimeError(
                    "Rate limited by Anthropic API after all retries. "
                    "Please wait before retrying."
                ) from e
                
        except anthropic.AuthenticationError as e:
            logger.error("Invalid API key or unauthorized")
            raise RuntimeError(
                "Authentication failed. Check your ANTHROPIC_API_KEY in .env"
            ) from e
            
        except anthropic.APIStatusError as e:
            logger.error(f"API error: {e.status_code} {e.message}")
            raise RuntimeError(
                f"Anthropic API error: {e.status_code} {e.message}"
            ) from e


def stream_claude(
    prompt: str,
    system: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
) -> Iterator[str]:
    """
    Yield text chunks from a streaming Claude response.
    
    Args:
        prompt: User message/question
        system: System prompt/instructions
        model: Claude model identifier
        max_tokens: Maximum tokens in response
        
    Yields:
        Text chunks from Claude's response
    """
    client = get_client()
    try:
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except anthropic.RateLimitError:
        logger.error("Rate limited during streaming")
        raise RuntimeError("Rate limited by API during streaming")
    except anthropic.APIStatusError as e:
        logger.error(f"Streaming API error: {e.status_code}")
        raise RuntimeError(f"API error during streaming: {e.status_code}")
