
"""Unified data models for LinkedIn Agent Suite."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

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
    location: str | None = None
    duration: str | None = None
    description: str = ""
    bullets: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    school: str = ""
    degree: str | None = None
    field_of_study: str | None = None
    duration: str | None = None


class Profile(BaseModel):
    urn_id: str | None = None
    username: str | None = None
    full_name: str = ""
    headline: str = ""
    location: str = ""
    about: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    profile_url: str | None = None
    featured_links: list[str] = Field(default_factory=list)
    custom_url: str | None = None
    scraped_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def full_text(self) -> str:
        parts = [
            self.full_name,
            self.headline,
            self.about,
            " ".join(self.skills),
            " ".join(self.languages),
        ]
        for exp in self.experience:
            parts.extend(
                [exp.title, exp.company, exp.description, " ".join(exp.bullets)]
            )
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
    posted_at: str | None = None
    tags: list[str] = Field(default_factory=list)
    salary: str | None = None
    apply_url: str | None = None
    scraped_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


JobPosting = Job


class JobFit(BaseModel):
    job_id: str
    title: str
    company: str
    url: str
    score: float = Field(ge=0.0, le=100.0)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
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
    fit_score: float | None = None
    notes: str = ""
    cover_note: str | None = ""
    applied_at: str | None = None
    follow_up_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


ApplicationRecord = ApplicationTrackerItem


class PostDraft(BaseModel):
    id: str
    source_type: str = "manual"
    topic: str
    hook: str
    body: str
    status: str = "DRAFT"
    approval_token: str | None = None
    scheduled_at: str | None = None
    published_at: str | None = None
    post_urn: str | None = None
    evidence: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class MessageThread(BaseModel):
    snippet: str | None = None
    thread_id: str
    participants: list[str] = Field(default_factory=list)
    last_message: str | None = None
    unread_count: int = 0


class PublishResult(BaseModel):
    status: str
    post_urn: str | None = None
    http_status: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    is_confirmed: bool = False
    published_at: str | None = None

