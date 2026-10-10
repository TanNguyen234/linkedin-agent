"""Interpretable multi-factor job fit ranker with grounded evidence mapping."""

from __future__ import annotations

import re

from ...core.models import Job, JobFit, Profile


def parse_experience_years(profile: Profile) -> float | None:
    """Extract actual total years of experience from experience duration strings."""
    total_months = 0
    found_any_duration = False

    for exp in profile.experience:
        if not exp.duration:
            continue
        dur = exp.duration.lower()
        years_match = re.search(r"(\d+)\s*(?:yr|year|yrs|years)", dur)
        months_match = re.search(r"(\d+)\s*(?:mo|month|mos|months)", dur)

        exp_m = 0
        if years_match:
            exp_m += int(years_match.group(1)) * 12
            found_any_duration = True
        if months_match:
            exp_m += int(months_match.group(1))
            found_any_duration = True

        total_months += exp_m

    if not found_any_duration:
        # Cannot determine years from duration strings
        return None

    return total_months / 12.0


def extract_required_experience_years(jd_text: str) -> float | None:
    """Extract required years of experience from job description."""
    match = re.search(r"(\d+)\+?\s*(?:-\s*(\d+)\+?)?\s*(?:years|yrs)\s*(?:of)?\s*(?:experience|exp)", jd_text.lower())
    if match:
        return float(match.group(1))
    return None


def score_job_fit(job: Job, profile: Profile) -> JobFit:
    """Compute evidence-backed multi-factor job fit score."""
    jd_text = (job.title + " " + job.description).lower()
    profile_text = profile.full_text().lower()

    # 1. Technical Skills Score (30%)
    tech_skills = [
        "python",
        "typescript",
        "javascript",
        "react",
        "fastapi",
        "django",
        "docker",
        "llm",
        "rag",
        "sql",
        "postgres",
        "aws",
        "gcp",
        "azure",
        "kubernetes",
        "git",
    ]
    jd_skills = [s for s in tech_skills if re.search(rf"\b{re.escape(s)}\b", jd_text)]
    profile_skills = set(s.lower() for s in profile.skills).union(
        set(s for s in tech_skills if re.search(rf"\b{re.escape(s)}\b", profile_text))
    )

    matched_skills = [s for s in jd_skills if s in profile_skills]
    missing_skills = [s for s in jd_skills if s not in profile_skills]

    if jd_skills:
        skill_score = (len(matched_skills) / len(jd_skills)) * 100.0
    else:
        # Check if any profile skills appear in JD
        matched_any = [s for s in profile.skills if s.lower() in jd_text]
        skill_score = 50.0 if matched_any else 0.0

    # 2. Title & Seniority Match (25%)
    role_tokens = set(re.findall(r"\b[a-z]{3,}\b", profile.headline.lower()))
    job_tokens = set(re.findall(r"\b[a-z]{3,}\b", job.title.lower()))
    has_role_overlap = bool(role_tokens & job_tokens)

    seniority_levels = ["intern", "junior", "mid", "senior", "lead", "staff", "principal", "architect", "director"]
    job_seniorities = [lvl for lvl in seniority_levels if re.search(rf"\b{re.escape(lvl)}\b", job.title.lower())]
    profile_seniorities = [lvl for lvl in seniority_levels if re.search(rf"\b{re.escape(lvl)}\b", profile.headline.lower())]

    title_match = False
    if not has_role_overlap and skill_score == 0:
        seniority_score = 0.0
    elif job_seniorities and profile_seniorities:
        if job_seniorities[0] == profile_seniorities[0]:
            seniority_score = 100.0
            title_match = True
        else:
            seniority_score = 40.0
    elif has_role_overlap:
        seniority_score = 80.0
        title_match = True
    else:
        seniority_score = 30.0


    # 3. Experience Match (15%) - Never use len(experience)
    actual_years = parse_experience_years(profile)
    req_years = extract_required_experience_years(jd_text)

    if actual_years is not None and req_years is not None:
        if actual_years >= req_years:
            exp_score = 100.0
        else:
            exp_score = max(30.0, (actual_years / req_years) * 100.0)
    elif actual_years is not None:
        # General career progression curve
        exp_score = min(100.0, 50.0 + (actual_years * 10.0))
    else:
        # Unknown duration: neutral score based on role presence
        exp_score = 70.0 if profile.experience else 40.0

    # 4. Location Match (15%)
    job_loc = job.location.lower()
    prof_loc = profile.location.lower()

    if "remote" in job_loc:
        loc_score = 100.0
    elif not job_loc:
        loc_score = 80.0
    elif prof_loc and (job_loc in prof_loc or prof_loc in job_loc):
        loc_score = 100.0
    else:
        loc_score = 50.0

    # 5. Education & Language Match (15%)
    edu_score = 80.0
    if "phd" in jd_text:
        has_phd = any("phd" in (e.degree or "").lower() or "doctor" in (e.degree or "").lower() for e in profile.education)
        edu_score = 100.0 if has_phd else 50.0
    elif "master" in jd_text:
        has_ms = any("master" in (e.degree or "").lower() or "ms" in (e.degree or "").lower() for e in profile.education)
        edu_score = 100.0 if has_ms else 60.0
    elif profile.education:
        edu_score = 90.0

    # Weighted Overall Score
    overall_score = (
        skill_score * 0.30
        + seniority_score * 0.25
        + exp_score * 0.15
        + loc_score * 0.15
        + edu_score * 0.15
    )
    overall_score = round(max(0.0, min(100.0, overall_score)), 1)

    exp_desc = f"{actual_years:.1f} yrs" if actual_years is not None else "duration not specified"
    rationale = (
        f"Skills: {len(matched_skills)}/{len(jd_skills)} matched ({skill_score:.0f}%). "
        f"Seniority: {seniority_score:.0f}%. Experience: {exp_desc} ({exp_score:.0f}%). "
        f"Location: {loc_score:.0f}%. Education: {edu_score:.0f}%."
    )

    return JobFit(
        job_id=job.id,
        title=job.title,
        company=job.company,
        url=job.url,
        score=overall_score,
        matched_keywords=matched_skills,
        missing_keywords=missing_skills,
        title_match=title_match,
        rationale=rationale,
    )
