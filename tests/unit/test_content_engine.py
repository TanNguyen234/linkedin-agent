"""Unit tests for content generation, humanizer, and validator."""
from src.intelligence.content.humanizer import humanize_text
from src.intelligence.content.validator import validate_claims
from src.intelligence.content.post_generator import create_post_draft

def test_humanizer_removes_cliches():
    text = "Let us delve into this game changer! It is a tapestry of innovation."
    cleaned = humanize_text(text)
    assert "delve" not in cleaned.lower()
    assert "game changer" not in cleaned.lower()
    assert "tapestry" not in cleaned.lower()

def test_validator_detects_unverified_numbers():
    body = "Our project increased revenue by 400% and saved $500,000."
    valid, warnings = validate_claims(body, source_facts=["We optimized speed"])
    assert valid is False
    assert len(warnings) >= 1

def test_post_generator():
    draft = create_post_draft("System Architecture", context_facts=["Production benchmarks"])
    assert draft.id.startswith("post-")
    assert draft.topic == "System Architecture"
    assert len(draft.hook) > 10
