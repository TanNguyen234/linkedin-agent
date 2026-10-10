"""Comprehensive unit tests for evidence-aware job fit ranking."""

from linkedin_agent_suite.core.models import EducationItem, ExperienceItem, Job, Profile
from linkedin_agent_suite.intelligence.jobs.ranker import (
    parse_experience_years,
    score_job_fit,
)


def test_experience_duration_parsing_not_item_count():
    # 5 short internships (2 mos each = 10 mos = ~0.83 yr)
    profile_internships = Profile(
        experience=[
            ExperienceItem(title="Intern 1", duration="2 mos"),
            ExperienceItem(title="Intern 2", duration="2 mos"),
            ExperienceItem(title="Intern 3", duration="2 mos"),
            ExperienceItem(title="Intern 4", duration="2 mos"),
            ExperienceItem(title="Intern 5", duration="2 mos"),
        ]
    )
    years = parse_experience_years(profile_internships)
    assert years is not None
    assert round(years, 2) == 0.83  # Not 5 years!

    # 1 long role of 6 years
    profile_senior = Profile(
        experience=[
            ExperienceItem(title="Senior Engineer", duration="6 yrs"),
        ]
    )
    years_senior = parse_experience_years(profile_senior)
    assert years_senior == 6.0


def test_missing_dates_returns_none_duration():
    profile = Profile(
        experience=[
            ExperienceItem(title="Software Engineer", company="Tech Corp"),
        ]
    )
    assert parse_experience_years(profile) is None


def test_senior_role_with_junior_profile_penalized():
    junior_profile = Profile(
        headline="Junior Python Developer",
        experience=[ExperienceItem(duration="1 yr")],
    )
    senior_job = Job(
        id="job-senior",
        title="Senior Lead Software Architect",
        company="Enterprise",
        url="https://example.com/job/senior",
        description="Requires 7+ years of experience in distributed systems.",
    )
    fit = score_job_fit(senior_job, junior_profile)
    assert fit.title_match is False
    assert fit.score < 65.0


def test_location_mismatch():
    profile = Profile(location="Tokyo, Japan")
    job = Job(
        id="job-loc",
        title="Software Engineer",
        company="Local Co",
        location="Austin, TX",
        url="https://example.com/job/loc",
        description="Onsite presence required in Austin.",
    )
    fit = score_job_fit(job, profile)
    assert "Location: 50%" in fit.rationale


def test_education_requirement_degree_level():
    profile_bs = Profile(
        education=[EducationItem(school="State Univ", degree="Bachelor of Science")]
    )
    job_phd = Job(
        id="job-phd",
        title="Research Scientist",
        company="AI Lab",
        url="https://example.com/job/phd",
        description="PhD in Computer Science required.",
    )
    fit = score_job_fit(job_phd, profile_bs)
    assert "Education: 50%" in fit.rationale


def test_job_fit_scoring_aligned():
    profile = Profile(
        headline="Senior AI Systems Engineer",
        about="Building LLM pipelines with Python and RAG.",
        skills=["Python", "LLM", "RAG", "FastAPI"],
        experience=[ExperienceItem(duration="5 yrs")],
        education=[EducationItem(school="Tech Univ", degree="Master of Science")],
        location="Remote",
    )
    job = Job(
        id="job-1",
        title="Senior AI Systems Engineer",
        company="AI Labs",
        location="Remote",
        url="https://example.com/job/1",
        description="Seeking Senior AI Engineer with Python, LLM, RAG, and FastAPI. 4+ years of experience required.",
    )
    fit = score_job_fit(job, profile)
    assert fit.score >= 80.0
    assert fit.title_match is True
    assert "python" in fit.matched_keywords
    assert "rag" in fit.matched_keywords
