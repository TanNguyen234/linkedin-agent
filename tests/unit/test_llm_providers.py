"""Unit tests for configurable LLM providers."""

from linkedin_agent_suite.intelligence.content.llm_provider import MockLLMProvider


def test_mock_provider():
    p = MockLLMProvider()
    res = p.generate("Explain RAG")
    assert "[TEMPLATE_FALLBACK]" in res
