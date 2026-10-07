"""Job Hunt Workflow: Search -> Deduplicate -> Rank -> Prepare."""
from typing import List, Dict, Any
from src.core.models.models import JobPosting, ProfileSnapshot
from src.intelligence.job_matching.ranker import score_job_fit
from src.intelligence.application.prep import prepare_application

def run_job_hunt_workflow(jobs: List[JobPosting], profile: ProfileSnapshot, min_score: int = 50) -> List[Dict[str, Any]]:
    # Deduplicate jobs by title + company
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
            scored.append({
                "job": j.dict(),
                "fit_score": fit.score,
                "missing_skills": fit.missing_keywords,
                "talking_points": app_prep["talking_points"]
            })
            
    scored.sort(key=lambda x: x["fit_score"], reverse=True)
    return scored
