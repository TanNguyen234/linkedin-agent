"""Unit tests for job fit ranking."""
from src.core.models.models import JobPosting, ProfileSnapshot
from src.intelligence.job_matching.ranker import score_job_fit

def test_job_fit_scoring():
    profile = ProfileSnapshot(
        headline="Agentic AI Engineer",
        about="Building LLM pipelines with Python and RAG.",
        skills=["Python", "LLM", "RAG", "Agentic"]
    )
    job = JobPosting(
        id="job-1",
        title="Senior AI Engineer",
        company="AI Labs",
        url="https://example.com/job/1",
        description="Looking for an AI engineer with strong Python, LLM, and agentic experience.",
        tags=["python", "ai", "llm"]
    )
    fit = score_job_fit(job, profile)
    assert fit.score >= 50
    assert fit.title_match is True
    assert "python" in fit.matched_keywords or "llm" in fit.matched_keywords
