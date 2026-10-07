"""Job application talking points and cover note drafting."""
from typing import Dict, Any
from src.core.models.models import JobPosting, ProfileSnapshot
from src.intelligence.job_matching.ranker import score_job_fit

def prepare_application(job: JobPosting, profile: ProfileSnapshot) -> Dict[str, Any]:
    fit = score_job_fit(job, profile)
    
    talking_points = [
        f"Demonstrated background in {', '.join(fit.matched_keywords[:4])} directly matching the role requirements.",
        "Hands-on experience delivering reliable, production-tested software with verifiable results.",
        "Commitment to pragmatic system design and continuous learning."
    ]
    
    cover_note = (
        f"Hi {job.company} Team,\n\n"
        f"I came across your opening for {job.title} and wanted to reach out. "
        f"My background in {', '.join(fit.matched_keywords[:3])} and scalable agentic systems aligns closely with what you are building.\n\n"
        f"I've previously engineered high-throughput services and practical AI workflows, focusing on measurable reliability. "
        f"I'd love the chance to discuss how my skill set can support your team's goals.\n\n"
        f"Best regards,\n{profile.name or 'Applicant'}"
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
