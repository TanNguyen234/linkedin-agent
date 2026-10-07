"""Configurable LLM Provider layer supporting Gemini, OpenAI, Local and Mock."""

from __future__ import annotations

import abc

import httpx

from ...core.config import Settings
from ...core.errors import AuthenticationError, ConfigurationError


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text from model."""


class MockLLMProvider(LLMProvider):
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return f"[TEMPLATE_FALLBACK] Strategic post insight: {prompt[:80]}..."


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        if not self.api_key:
            raise ConfigurationError("GEMINI_API_KEY required for GeminiProvider.")

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        parts = [{"text": prompt}]
        if system_prompt:
            parts.insert(0, {"text": f"System: {system_prompt}\n"})
        payload = {"contents": [{"parts": parts}]}
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                elif res.status_code in (401, 403):
                    raise AuthenticationError(f"Gemini API key invalid: {res.text}")
                else:
                    raise RuntimeError(
                        f"Gemini API error ({res.status_code}): {res.text}"
                    )
        except httpx.HTTPError as e:
            raise RuntimeError(f"Gemini connection failed: {e}")


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        if not self.api_key:
            raise ConfigurationError("OPENAI_API_KEY required for OpenAIProvider.")

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": messages},
                )
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
                elif res.status_code in (401, 403):
                    raise AuthenticationError(f"OpenAI API key invalid: {res.text}")
                else:
                    raise RuntimeError(f"OpenAI error ({res.status_code}): {res.text}")
        except httpx.HTTPError as e:
            raise RuntimeError(f"OpenAI connection failed: {e}")


class LocalProvider(LLMProvider):
    def __init__(
        self,
        base_url: str = "http://localhost:11434/api/generate",
        model: str = "llama3",
    ):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        with httpx.Client(timeout=60.0) as client:
            res = client.post(self.base_url, json=payload)
            if res.status_code == 200:
                return res.json().get("response", "")
            raise RuntimeError(f"Local LLM error: {res.text}")


def get_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider in ("gemini", "google"):
        key = settings.gemini_api_key or settings.llm_api_key or ""
        return GeminiProvider(key, settings.llm_model)
    elif provider in ("openai",):
        key = settings.openai_api_key or settings.llm_api_key or ""
        return OpenAIProvider(key, settings.llm_model)
    elif provider in ("local", "ollama"):
        return LocalProvider(model=settings.llm_model)
    return MockLLMProvider()
