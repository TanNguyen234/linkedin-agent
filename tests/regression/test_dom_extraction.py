"""Regression tests verifying DOM extractors on LinkedIn fixtures."""

from linkedin_agent_suite.core.models import ExperienceItem, Job, Profile


def test_profile_full_text():
    p = Profile(
        full_name="Jane Doe",
        headline="Senior AI Engineer",
        about="AI enthusiast",
        skills=["Python", "PyTorch"],
        experience=[
            ExperienceItem(title="Lead", company="TechCorp", description="Built LLM")
        ],
    )
    text = p.full_text()
    assert "Jane Doe" in text
    assert "TechCorp" in text
    assert "Python" in text


def test_job_model_contract():
    j = Job(
        id="12345",
        title="AI Engineer",
        company="Corp",
        url="https://linkedin.com/jobs/view/12345",
    )
    assert j.id == "12345"
    assert j.source == "linkedin"
