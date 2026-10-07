"""LLM Provider abstraction for content generation."""
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        pass

class MockLLMProvider(LLMProvider):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return "Deterministic generated response based on prompt context."
