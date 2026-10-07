"""5-dimension profile audit engine for LinkedIn optimization."""

from typing import Any

from ...core.models import Profile

TARGET_WEIGHTS = {
    "headline": 0.25,
    "about": 0.25,
    "skills": 0.20,
    "experience": 0.20,
    "completeness": 0.10,
}

ROLE_SKILLS = {
    "agentic-ai-systems-engineer": [
        "Python",
        "RAG",
        "Agentic",
        "LLM",
        "Docker",
        "FastAPI",
        "TypeScript",
        "Evaluation",
    ],
    "senior-full-stack-engineer": [
        "TypeScript",
        "React",
        "Node.js",
        "Python",
        "SQL",
        "Docker",
        "AWS",
        "CI/CD",
    ],
    "ai-automation-consultant": [
        "AI",
        "Automation",
        "Zapier",
        "Make",
        "Python",
        "LLM",
        "Workflow",
        "Consulting",
    ],
    "react-python-php-engineer": [
        "React",
        "Python",
        "PHP",
        "Laravel",
        "MySQL",
        "JavaScript",
        "HTML",
        "CSS",
    ],
}


def audit_profile(
    profile: Profile, target_role: str = "agentic-ai-systems-engineer"
) -> dict[str, Any]:
    expected_skills = ROLE_SKILLS.get(
        target_role, ROLE_SKILLS["agentic-ai-systems-engineer"]
    )
    profile_skills_lower = [s.lower() for s in profile.skills]

    # 1. Headline Score
    headline_score = 0
    if profile.headline:
        headline_score += 40
        if any(kw.lower() in profile.headline.lower() for kw in expected_skills[:3]):
            headline_score += 40
        if len(profile.headline) > 30:
            headline_score += 20
    headline_score = min(100, headline_score)

    # 2. About Score
    about_score = 0
    if profile.about:
        about_score += 30
        if len(profile.about) >= 150:
            about_score += 40
        if any(
            term in profile.about.lower()
            for term in ["build", "architect", "lead", "engineer", "develop"]
        ):
            about_score += 30
    about_score = min(100, about_score)

    # 3. Skills Score
    matched_skills = [s for s in expected_skills if s.lower() in profile_skills_lower]
    skills_score = int((len(matched_skills) / max(1, len(expected_skills))) * 100)
    skills_score = min(100, skills_score)

    # 4. Experience Score
    exp_score = 0
    if profile.experience:
        exp_score += 40
        has_metrics = False
        for exp in profile.experience:
            text = f"{exp.description} {' '.join(exp.bullets)}"
            if any(char.isdigit() for char in text):
                has_metrics = True
                break
        if has_metrics:
            exp_score += 40
        if len(profile.experience) >= 2:
            exp_score += 20
    exp_score = min(100, exp_score)

    # 5. Completeness Score
    comp_score = 0
    if profile.full_name:
        comp_score += 20
    if profile.headline:
        comp_score += 20
    if profile.about:
        comp_score += 20
    if profile.skills:
        comp_score += 20
    if profile.experience:
        comp_score += 20

    overall = int(
        headline_score * TARGET_WEIGHTS["headline"]
        + about_score * TARGET_WEIGHTS["about"]
        + skills_score * TARGET_WEIGHTS["skills"]
        + exp_score * TARGET_WEIGHTS["experience"]
        + comp_score * TARGET_WEIGHTS["completeness"]
    )

    return {
        "overall": overall,
        "target_role": target_role,
        "dimensions": [
            {"dimension": "Recruiter searchability", "score": headline_score},
            {"dimension": "Structural clarity", "score": about_score},
            {
                "dimension": "Role keyword density",
                "score": skills_score,
                "matched": matched_skills,
            },
            {"dimension": "Credibility & Metrics", "score": exp_score},
            {"dimension": "Action-oriented language", "score": comp_score},
        ],
    }
