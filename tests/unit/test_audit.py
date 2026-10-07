"""Unit tests for 5-dimension profile audit engine."""
from src.core.models.models import ProfileSnapshot, ExperienceItem
from src.intelligence.profile.audit import audit_profile

def test_audit_profile_scoring():
    profile = ProfileSnapshot(
        name="Test Engineer",
        headline="Senior Agentic AI Systems Engineer",
        about="Passionate software engineer building stuff. DM me to connect.",
        skills=["Python", "LLM", "Agentic", "RAG", "MCP", "Docker"],
        experience=[
            ExperienceItem(
                title="AI Engineer",
                company="TechCorp",
                bullets=["Built agentic workflow reducing latency by 45%", "Scaled system to 100k users"]
            )
        ],
        custom_url="linkedin.com/in/test"
    )
    res = audit_profile(profile, target_role="agentic-ai-systems-engineer")
    assert res["overall"] > 50
    assert len(res["dimensions"]) == 5
    dims = {d["dimension"]: d["score"] for d in res["dimensions"]}
    assert "Recruiter searchability" in dims
    assert "Clarity" in dims
    assert "Credibility & Metrics" in dims
    assert dims["Credibility & Metrics"] > 70
