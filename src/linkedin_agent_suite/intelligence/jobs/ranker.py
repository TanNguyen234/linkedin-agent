"""Interpretable multi-factor job fit ranker."""

from __future__ import annotations

import re

from ...core.models import Job, JobFit, Profile


def score_job_fit(job: Job, profile: Profile) -> JobFit:
    text = (job.title + " " + job.description).lower()
    profile_text = profile.full_text().lower()

    # 1. Technical Skills Score (30%)
    tech_skills = [
        "python",
        "typescript",
        "react",
        "fastapi",
        "docker",
        "llm",
        "rag",
        "sql",
        "aws",
        "kubernetes",
    ]
    matched_skills = [s for s in tech_skills if s in text and s in profile_text]
    missing_skills = [s for s in tech_skills if s in text and s not in profile_text]
    total_skills = len(matched_skills) + len(missing_skills)
    skill_score = (
        (len(matched_skills) / max(1, total_skills)) * 100 if total_skills > 0 else 70.0
    )

    # 2. Title & Seniority Match (25%)
    seniority_levels = ["senior", "lead", "staff", "principal", "architect"]
    job_seniority = any(lvl in job.title.lower() for lvl in seniority_levels)
    profile_seniority = any(lvl in profile.headline.lower() for lvl in seniority_levels)
    seniority_score = (
        100.0
        if (job_seniority == profile_seniority)
        else (60.0 if not job_seniority else 40.0)
    )

    # 3. Experience Match (15%)
    exp_years = len(profile.experience)
    exp_score = min(100.0, exp_years * 20.0)

    # 4. Location Match (15%)
    loc_score = (
        100.0
        if (
            "remote" in job.location.lower()
            or "remote" in profile.location.lower()
            or not job.location
        )
        else 70.0
    )

    # 5. Language & Education Match (15%)
    edu_score = 85.0 if profile.education else 60.0

    title_match = bool(
        re.search(
            r"(ai|systems|software|engineer|lead|architect)", job.title, re.IGNORECASE
        )
    )

    if not matched_skills and not title_match:
        overall = 15.0
    else:
        overall = (
            skill_score * 0.30
            + seniority_score * 0.25
            + exp_score * 0.15
            + loc_score * 0.15
            + edu_score * 0.15
        )

    rationale = f"Skills match: {len(matched_skills)}/{total_skills}. Seniority alignment: {int(seniority_score)}%."

    return JobFit(
        job_id=job.id,
        title=job.title,
        company=job.company,
        url=job.url,
        score=round(overall, 1),
        matched_keywords=matched_skills,
        missing_keywords=missing_skills,
        title_match=title_match,
        rationale=rationale,
    )
