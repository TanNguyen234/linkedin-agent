"""Evidence-grounded application prep without fabricated metrics."""
from typing import Dict, Any
from ...core.models import Job, Profile
from ..jobs.ranker import score_job_fit

def prepare_application(job: Job, profile: Profile) -> Dict[str, Any]:
    fit = score_job_fit(job, profile)
    
    talking_points = []
    if fit.matched_keywords:
        talking_points.append(f"Demonstrated background in {', '.join(fit.matched_keywords[:3])}.")
    if profile.experience:
        talking_points.append(f"Hands-on experience at {profile.experience[0].company} as {profile.experience[0].title}.")
    
    cover_note = (
        f"Hi {job.company} Team,\n\n"
        f"I am applying for the {job.title} position. "
        f"My background in {', '.join(fit.matched_keywords[:3]) if fit.matched_keywords else 'software engineering'} "
        f"aligns with your technical focus.\n\n"
        f"Best regards,\n{profile.full_name or 'Applicant'}"
    )
    
    return {
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "apply_url": job.url,
        "fit_score": fit.score,
        "talking_points": talking_points,
        "cover_note": cover_note
    }
