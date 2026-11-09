"""
LLM Provider abstraction.

Design goal: the rest of the app calls `llm_router.generate(system_prompt, user_prompt)`
and never knows which underlying API served the request. Providers are tried in the
order configured in LLM_PROVIDER_ORDER, falling back automatically on:
  - missing/invalid API key
  - rate limit / quota exhaustion (HTTP 429)
  - timeout
  - provider downtime (5xx)

Add a new provider by implementing BaseLLMProvider and registering it in PROVIDER_REGISTRY.
"""
from __future__ import annotations
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import httpx

from backend.config import settings

logger = logging.getLogger("llm_provider")


class LLMProviderError(Exception):
    """Raised for retryable provider failures (timeout/429/5xx/auth)."""


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    latency_ms: float


class BaseLLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    def _call(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        ...

    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 700, temperature: float = 0.3) -> LLMResponse:
        if not self.is_configured():
            raise LLMProviderError(f"{self.name} is not configured (missing API key)")
        start = time.time()
        try:
            text = self._call(system_prompt, user_prompt, max_tokens, temperature)
        except httpx.TimeoutException as e:
            raise LLMProviderError(f"{self.name} timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code == 429:
                raise LLMProviderError(f"{self.name} rate-limited (429)") from e
            if code in (401, 403):
                raise LLMProviderError(f"{self.name} invalid/unauthorized API key ({code})") from e
            if code >= 500:
                raise LLMProviderError(f"{self.name} server error ({code})") from e
            raise LLMProviderError(f"{self.name} HTTP error {code}: {e}") from e
        except httpx.RequestError as e:
            raise LLMProviderError(f"{self.name} network error: {e}") from e
        latency_ms = (time.time() - start) * 1000
        return LLMResponse(text=text, provider=self.name, model=self.model, latency_ms=latency_ms)


class GroqProvider(BaseLLMProvider):
    name = "groq"
    model = settings.GROQ_MODEL

    def is_configured(self) -> bool:
        return bool(settings.GROQ_API_KEY)

    def _call(self, system_prompt, user_prompt, max_tokens, temperature) -> str:
        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class GeminiProvider(BaseLLMProvider):
    name = "gemini"
    model = settings.GEMINI_MODEL

    def is_configured(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def _call(self, system_prompt, user_prompt, max_tokens, temperature) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={settings.GEMINI_API_KEY}"
        resp = httpx.post(
            url,
            json={
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


class OpenRouterProvider(BaseLLMProvider):
    name = "openrouter"
    model = settings.OPENROUTER_MODEL

    def is_configured(self) -> bool:
        return bool(settings.OPENROUTER_API_KEY)

    def _call(self, system_prompt, user_prompt, max_tokens, temperature) -> str:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


PROVIDER_REGISTRY = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
}


class LLMRouter:
    """Tries providers in configured order, falling back on failure."""

    def __init__(self):
        self.providers = []
        for name in settings.LLM_PROVIDER_ORDER:
            cls = PROVIDER_REGISTRY.get(name)
            if cls:
                self.providers.append(cls())
        if not self.providers:
            logger.warning("No LLM providers registered. Check LLM_PROVIDER_ORDER.")

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> LLMResponse:
        last_error: Optional[Exception] = None
        for provider in self.providers:
            if not provider.is_configured():
                continue
            try:
                return provider.generate(system_prompt, user_prompt, **kwargs)
            except LLMProviderError as e:
                logger.warning("Provider %s failed, falling back: %s", provider.name, e)
                last_error = e
                continue
        raise LLMProviderError(
            f"All configured LLM providers failed or are unconfigured. Last error: {last_error}"
        )


llm_router = LLMRouter()
