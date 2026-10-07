"""Unit tests for job fit ranking."""

from linkedin_agent_suite.core.models import Job, Profile
from linkedin_agent_suite.intelligence.jobs.ranker import score_job_fit


def test_job_fit_scoring():
    profile = Profile(
        headline="Agentic AI Engineer",
        about="Building LLM pipelines with Python and RAG.",
        skills=["Python", "LLM", "RAG", "Agentic"],
    )
    job = Job(
        id="job-1",
        title="Senior AI Engineer",
        company="AI Labs",
        url="https://example.com/job/1",
        description="Looking for an AI engineer with strong Python, LLM, and agentic experience.",
        tags=["python", "ai", "llm"],
    )
    fit = score_job_fit(job, profile)
    assert fit.score >= 50
    assert fit.title_match is True
