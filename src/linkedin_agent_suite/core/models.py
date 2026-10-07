"""Unified data models for LinkedIn Agent Suite."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class TargetRole(str, Enum):
    AGENTIC_AI_SYSTEMS_ENGINEER = "agentic-ai-systems-engineer"
    SENIOR_FULL_STACK_ENGINEER = "senior-full-stack-engineer"
    AI_AUTOMATION_CONSULTANT = "ai-automation-consultant"
    REACT_PYTHON_PHP_ENGINEER = "react-python-php-engineer"

class ApplicationStatus(str, Enum):
    SAVED = "saved"
    PREPARING = "preparing"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class ExperienceItem(BaseModel):
    title: str = ""
    company: str = ""
    location: Optional[str] = None
    duration: Optional[str] = None
    description: str = ""
    bullets: List[str] = Field(default_factory=list)

class EducationItem(BaseModel):
    school: str = ""
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    duration: Optional[str] = None

class Profile(BaseModel):
    urn_id: Optional[str] = None
    username: Optional[str] = None
    full_name: str = ""
    headline: str = ""
    location: str = ""
    about: str = ""
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    profile_url: Optional[str] = None
    featured_links: List[str] = Field(default_factory=list)
    custom_url: Optional[str] = None
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def full_text(self) -> str:
        parts = [
            self.full_name, self.headline, self.about,
            " ".join(self.skills), " ".join(self.languages)
        ]
        for exp in self.experience:
            parts.extend([exp.title, exp.company, exp.description, " ".join(exp.bullets)])
        for edu in self.education:
            parts.extend([edu.school, edu.degree or "", edu.field_of_study or ""])
        return "\n".join(filter(None, parts))

ProfileSnapshot = Profile

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str = "Remote"
    description: str = ""
    url: str
    source: str = "linkedin"
    posted_at: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    salary: Optional[str] = None
    apply_url: Optional[str] = None
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

JobPosting = Job

class JobFit(BaseModel):
    job_id: str
    title: str
    company: str
    url: str
    score: float = Field(ge=0.0, le=100.0)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    title_match: bool = False
    rationale: str = ""

JobFitScore = JobFit

class ApplicationTrackerItem(BaseModel):
    id: str
    job_id: str
    company: str
    title: str
    url: str
    status: ApplicationStatus = ApplicationStatus.SAVED
    fit_score: Optional[float] = None
    notes: str = ""
    cover_note: Optional[str] = ""
    applied_at: Optional[str] = None
    follow_up_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

ApplicationRecord = ApplicationTrackerItem

class PostDraft(BaseModel):
    id: str
    source_type: str = "manual"
    topic: str
    hook: str
    body: str
    status: str = "DRAFT"
    approval_token: Optional[str] = None
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    post_urn: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MessageThread(BaseModel):
    thread_id: str
    participants: List[str] = Field(default_factory=list)
    last_message: Optional[str] = None
    unread_count: int = 0
