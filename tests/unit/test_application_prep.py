"""Unit tests for evidence-grounded application prep."""

from linkedin_agent_suite.core.models import ExperienceItem, Job, Profile
from linkedin_agent_suite.intelligence.application.prep import (
    EvidenceLevel,
    prepare_application,
)


def test_prep_skill_only_does_not_fabricate_production_proficiency():
    profile = Profile(
        full_name="Alex Developer",
        skills=["Python", "Docker"],
        experience=[],  # No experience entries
    )
    job = Job(
        id="job-1",
        title="Python Developer",
        company="Startup Co",
        url="https://example.com/job/1",
        description="Looking for Python and Docker developer.",
    )
    prep = prepare_application(job, profile)

    claims = prep["claims"]
    py_claim = next(c for c in claims if c["requirement"] == "Python")

    # Must be PROFILE_SKILL_ONLY, NOT claiming production proficiency
    assert py_claim["evidence_level"] == EvidenceLevel.PROFILE_SKILL_ONLY.value
    assert "Hands-on production proficiency" not in py_claim["claim"]
    assert "profile skill set" in py_claim["claim"]

    # Cover note must not contain grandiose fabricated claims
    assert "architecting reliable production solutions" not in prep["pitch"]


def test_prep_verified_experience_recognized():
    profile = Profile(
        full_name="Senior Engineer",
        skills=["Python", "FastAPI"],
        experience=[
            ExperienceItem(
                title="Lead Backend Engineer",
                company="FinTech Ltd",
                description="Built high-throughput financial microservices using Python and FastAPI.",
            )
        ],
    )
    job = Job(
        id="job-2",
        title="Senior Python Engineer",
        company="Global Payments",
        url="https://example.com/job/2",
        description="Seeking Python and FastAPI specialist. Kubernetes required.",
    )
    prep = prepare_application(job, profile)

    claims = prep["claims"]
    py_claim = next(c for c in claims if c["requirement"] == "Python")
    assert py_claim["evidence_level"] == EvidenceLevel.VERIFIED_PROJECT_OR_EXPERIENCE.value
    assert "Lead Backend Engineer at FinTech Ltd" in py_claim["evidence_source"]

    # Missing kubernetes must be flagged as UNSUPPORTED
    k8s_claim = next((c for c in claims if c["requirement"] == "kubernetes"), None)
    assert k8s_claim is not None
    assert k8s_claim["evidence_level"] == EvidenceLevel.UNSUPPORTED.value
    assert "kubernetes" in prep["missing_requirements"]
