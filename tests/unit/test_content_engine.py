"""Unit tests for content generation, humanizer, and validator."""
from linkedin_agent_suite.intelligence.content.humanizer import humanize_text, quality_report
from linkedin_agent_suite.intelligence.content.validator import validate_claims
from linkedin_agent_suite.intelligence.content.post_generator import create_post_draft
from linkedin_agent_suite.intelligence.content.topic_selector import extract_from_git

def test_humanizer():
    text = "Let us delve into this game changer! It is a tapestry of innovation."
    cleaned = humanize_text(text)
    assert "delve" not in cleaned.lower()
    assert "game changer" not in cleaned.lower()
    report = quality_report(cleaned)
    assert report["is_clean"] is True

def test_validator():
    body = "Our project increased revenue by 400% and saved $500,000."
    valid, warnings = validate_claims(body, source_facts=["We optimized speed"])
    assert valid is False
    assert len(warnings) >= 1

def test_post_generator():
    draft = create_post_draft("System Architecture", context_facts=["Production benchmarks"])
    assert draft.id.startswith("post-")
    assert draft.topic == "System Architecture"

def test_topic_extractor_no_evidence():
    res = extract_from_git("non_existent_folder_xyz_123")
    assert res["status"] == "NO_EVIDENCE"
