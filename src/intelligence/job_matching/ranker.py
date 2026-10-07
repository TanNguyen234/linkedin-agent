"""Job fit scoring engine."""
from typing import List
from src.core.models.models import JobPosting, JobFitScore, ProfileSnapshot
from src.intelligence.profile.keywords import extract_keywords_from_jd, keyword_coverage

TITLE_HINTS = [
    "full stack", "fullstack", "software engineer", "ai", "agent", "llm",
    "automation", "react", "python", "php", "typescript", "senior", "founding"
]

def score_job_fit(job: JobPosting, profile: ProfileSnapshot) -> JobFitScore:
    jd_text = f"{job.title}\n{' '.join(job.tags)}\n{job.description}"
    jd_kws = extract_keywords_from_jd(jd_text, limit=30)
    
    profile_text = f"{profile.headline}\n{profile.about}\n" + "\n".join(
        [f"{e.title} {' '.join(e.bullets)}" for e in profile.experience]
    ) + "\n" + " ".join(profile.skills)
    
    cov = keyword_coverage(profile_text, jd_kws)
    t = job.title.lower()
    title_hits = sum(1 for h in TITLE_HINTS if h in t)
    title_match = title_hits > 0
    
    final_score = int(min(100, round(cov["score"] * 0.75 + min(title_hits, 3) * 8 + (5 if title_match else 0))))
    
    return JobFitScore(
        job_id=job.id,
        title=job.title,
        company=job.company,
        url=job.url,
        score=final_score,
        matched_keywords=cov["present"][:10],
        missing_keywords=cov["missing"][:8],
        title_match=title_match
    )
