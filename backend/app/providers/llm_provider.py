"""LLM Provider abstraction for NEXUS.

Supports Gemini with easy extensibility to other providers.
Includes caching, rate limiting, retry logic, and structured output parsing.
"""
import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.3, use_fast: bool = False) -> str:
        """Generate text completion."""
        ...

    @abstractmethod
    async def structured_generate(self, prompt: str, response_model: Type[T],
                                   system_prompt: str = "", temperature: float = 0.1,
                                   use_fast: bool = False) -> T:
        """Generate structured output parsed into a Pydantic model."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        ...


class LLMCache:
    """Simple file-based LLM response cache."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / "llm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, prompt: str, system: str, model: str) -> str:
        content = f"{model}:{system}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, prompt: str, system: str, model: str) -> Optional[str]:
        key = self._key(prompt, system, model)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                logger.debug(f"Cache hit for {key[:8]}")
                return data.get("response")
            except Exception:
                return None
        return None

    def set(self, prompt: str, system: str, model: str, response: str):
        key = self._key(prompt, system, model)
        path = self.cache_dir / f"{key}.json"
        data = {"model": model, "response": response, "timestamp": time.time()}
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self.tokens: list[float] = []

    async def acquire(self):
        now = time.time()
        self.tokens = [t for t in self.tokens if now - t < 60]
        if len(self.tokens) >= self.max_per_minute:
            wait_time = 60 - (now - self.tokens[0]) + 0.1
            logger.info(f"Rate limit: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        self.tokens.append(time.time())


import random

class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider with semantic model routing and robust fault tolerance."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.gemini_api_key
        # Resolve reasoning model (GEMINI_REASONING_MODEL takes primary precedence)
        self.reasoning_model = settings.gemini_reasoning_model or settings.gemini_model or "gemini-3.7-flash"
        self.fast_model = settings.gemini_fast_model or "gemini-3.5-flash-lite"
        self.cache = LLMCache(settings.cache_dir)
        self.rate_limiter = RateLimiter(settings.llm_rate_limit_per_minute)
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_llm_calls)
        self._client = None

    @property
    def model(self) -> str:
        """Default reasoning model name."""
        return self.reasoning_model

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not configured in environment or .env file.")
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                logger.error("google-genai package not installed")
                raise
        return self._client

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.3, use_fast: bool = False,
                       response_mime_type: Optional[str] = None,
                       response_schema: Optional[Any] = None) -> str:
        target_model = self.fast_model if use_fast else self.reasoning_model

        # Check cache
        cached = self.cache.get(prompt, system_prompt, target_model)
        if cached:
            return cached

        await self.rate_limiter.acquire()
        client = self._get_client()

        from google.genai import types

        config_kwargs = {
            "temperature": temperature,
            "system_instruction": system_prompt if system_prompt else None,
        }
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type
        if response_schema:
            config_kwargs["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_kwargs)

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                async with self.semaphore:
                    response = await asyncio.to_thread(
                        client.models.generate_content,
                        model=target_model,
                        contents=prompt,
                        config=config,
                    )
                text = response.text or ""
                self.cache.set(prompt, system_prompt, target_model, text)
                return text
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str
                if attempt < max_attempts - 1:
                    base_wait = (2 ** attempt) * 2
                    jitter = random.uniform(0.5, 1.5)
                    wait = base_wait + jitter + (5.0 if is_rate_limit else 0.0)
                    logger.warning(
                        f"Gemini API error (model={target_model}, attempt {attempt + 1}/{max_attempts}, rate_limited={is_rate_limit}): {e}. Retrying in {wait:.1f}s"
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Gemini API failed after {max_attempts} attempts on model {target_model}: {e}")
                    raise

    async def structured_generate(self, prompt: str, response_model: Type[T],
                                   system_prompt: str = "", temperature: float = 0.1,
                                   use_fast: bool = False) -> T:
        """Generate structured output and parse into Pydantic model using native structured output."""
        
        raw = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            use_fast=use_fast,
            response_mime_type="application/json",
            response_schema=response_model
        )

        text = raw.strip()
        # Some fallback parsing in case the native output still has codeblocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        for attempt in range(2):
            try:
                data = json.loads(text)
                return response_model.model_validate(data)
            except (json.JSONDecodeError, Exception) as e:
                if attempt == 0:
                    logger.warning(f"Parse failed, attempting repair: {e}")
                    repair_prompt = (
                        f"The following text should be valid JSON but has errors. "
                        f"Fix it and return ONLY valid JSON:\n\n{text}"
                    )
                    text = await self.generate(repair_prompt, temperature=0.0, use_fast=True)
                    text = text.strip()
                    if text.startswith("```"):
                        lines = text.split("\n")
                        text = "\n".join(lines[1:])
                        if text.endswith("```"):
                            text = text[:-3]
                        text = text.strip()
                else:
                    logger.error(f"Structured output parse failed: {e}")
                    raise ValueError(f"Could not parse LLM output into {response_model.__name__}: {e}")

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.fast_model,
                contents="Say 'ok'",
            )
            return bool(response.text)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


class DemoLLMProvider(LLMProvider):
    """Demo LLM provider that returns pre-configured responses."""

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.3, use_fast: bool = False) -> str:
        return '{"status": "demo_mode"}'

    async def structured_generate(self, prompt: str, response_model: Type[T],
                                   system_prompt: str = "", temperature: float = 0.1,
                                   use_fast: bool = False) -> T:
        # Return default instance
        return response_model()

    async def health_check(self) -> bool:
        return True


_provider: Optional[LLMProvider] = None

def reset_llm_provider():
    """Invalidate the LLM provider singleton to force re-evaluation of settings."""
    global _provider
    _provider = None

def get_llm_provider() -> LLMProvider:
    """Get the LLM provider singleton."""
    global _provider
    if _provider is None:
        settings = get_settings()
        if settings.demo_mode:
            _provider = DemoLLMProvider()
            logger.info("Using Demo LLM Provider")
        else:
            if not settings.gemini_api_key:
                logger.warning("Live mode active but no Gemini API key found!")
            _provider = GeminiProvider()
            logger.info("Using Gemini LLM Provider")
    return _provider
