"""Job hunt workflow: search, deduplicate, rank, prepare."""

from typing import Any

from ..core.models import Job, Profile
from ..intelligence.application.prep import prepare_application
from ..intelligence.jobs.ranker import score_job_fit


def run_job_hunt_workflow(
    jobs: list[Job], profile: Profile, min_score: int = 40
) -> list[dict[str, Any]]:
    seen = set()
    unique_jobs = []
    for j in jobs:
        key = (j.title.lower().strip(), j.company.lower().strip())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(j)

    scored = []
    for j in unique_jobs:
        fit = score_job_fit(j, profile)
        if fit.score >= min_score:
            app_prep = prepare_application(j, profile)
            scored.append(
                {
                    "job": j.model_dump(),
                    "fit_score": fit.score,
                    "missing_skills": fit.missing_keywords,
                    "talking_points": app_prep["talking_points"],
                }
            )

    scored.sort(key=lambda x: x["fit_score"], reverse=True)
    return scored
