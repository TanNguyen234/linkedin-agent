"""Unified data models for LinkedIn Agent Suite."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class TargetRole(str, Enum):
    """Pre-curated target engineering roles for audits and optimizations."""
    AGENTIC_AI_SYSTEMS_ENGINEER = "agentic-ai-systems-engineer"
    SENIOR_FULL_STACK_ENGINEER = "senior-full-stack-engineer"
    AI_AUTOMATION_CONSULTANT = "ai-automation-consultant"
    REACT_PYTHON_PHP_ENGINEER = "react-python-php-engineer"
    MLOPS_PLATFORM_ENGINEER = "mlops-platform-engineer"


class ApplicationStatus(str, Enum):
    """Lifecycle status of a tracked job application."""
    SAVED = "saved"
    PREPARING = "preparing"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ExperienceItem(BaseModel):
    """Single career experience record."""
    title: str = ""
    company: str = ""
    location: str | None = None
    duration: str | None = None
    description: str = ""
    bullets: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    """Education record."""
    school: str = ""
    degree: str | None = None
    field_of_study: str | None = None
    duration: str | None = None


class Profile(BaseModel):
    """Normalized profile representation (from browser scrape or local text)."""
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
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def full_text(self) -> str:
        """Combine all profile text for keyword scanning."""
        parts = [
            self.full_name,
            self.headline,
            self.about,
            " ".join(self.skills),
            " ".join(self.languages),
        ]
        for exp in self.experience:
            parts.extend([exp.title, exp.company, exp.description, " ".join(exp.bullets)])
        for edu in self.education:
            parts.extend([edu.school, edu.degree or "", edu.field_of_study or ""])
        return "\n".join(filter(None, parts))


class Job(BaseModel):
    """Unified job listing schema across LinkedIn and remote job APIs."""
    id: str
    title: str
    company: str
    location: str = ""
    description: str = ""
    url: str
    source: str = "linkedin"  # 'linkedin', 'remotive', 'remoteok', 'manual'
    posted_at: str | None = None
    tags: list[str] = Field(default_factory=list)
    salary: str | None = None
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobFit(BaseModel):
    """Result of scoring a job against a candidate profile."""
    job_id: str
    title: str
    company: str
    url: str
    score: float = Field(ge=0.0, le=100.0)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    title_match: bool = False
    rationale: str = ""


class AuditDimension(BaseModel):
    """Evaluation score and feedback for a specific profile dimension."""
    dimension: str
    score: int = Field(ge=0, le=100)
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AuditResult(BaseModel):
    """Full 5-dimension profile audit output."""
    target_role: str
    overall_score: int = Field(ge=0, le=100)
    dimensions: list[AuditDimension] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    priority_improvements: list[str] = Field(default_factory=list)


class ApplicationPrep(BaseModel):
    """Tailored application preparation material."""
    job_id: str
    job_title: str
    company: str
    apply_url: str
    fit_score: float
    fit_summary: str
    talking_points: list[str] = Field(default_factory=list)
    cover_note: str = ""
    missing_skills: list[str] = Field(default_factory=list)


class ApplicationTrackerItem(BaseModel):
    """An entry in the local application tracker."""
    job_id: str
    title: str
    company: str
    url: str
    status: ApplicationStatus = ApplicationStatus.SAVED
    fit_score: float | None = None
    notes: str = ""
    applied_at: str | None = None
    follow_up_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UpdatePatchItem(BaseModel):
    """A proposed change to a specific field on the LinkedIn profile."""
    field: str
    edit_url: str
    old_text: str
    new_text: str
    rationale: str


class UpdatePlan(BaseModel):
    """A complete plan for improving the LinkedIn profile."""
    target_role: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    patches: list[UpdatePatchItem] = Field(default_factory=list)
