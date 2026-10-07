"""Pydantic data models for LinkedIn Agent Suite."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ExperienceItem(BaseModel):
    title: str
    company: str
    date_range: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = ""
    bullets: List[str] = Field(default_factory=list)

class ProfileSnapshot(BaseModel):
    name: Optional[str] = "AI Engineer"
    headline: str
    about: str
    custom_url: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    featured_links: List[str] = Field(default_factory=list)

class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str] = "Remote"
    url: str
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    source: str = "linkedin"  # linkedin, remotive, remoteok

class JobFitScore(BaseModel):
    job_id: str
    title: str
    company: str
    url: str
    score: int  # 0 - 100
    matched_keywords: List[str]
    missing_keywords: List[str]
    title_match: bool

class ApplicationRecord(BaseModel):
    id: str
    job_id: str
    company: str
    title: str
    status: str = "SAVED"  # SAVED, APPLIED, INTERVIEWING, OFFER, REJECTED
    apply_url: str
    notes: Optional[str] = ""
    cover_note: Optional[str] = ""
    created_at: str
    updated_at: str

class PostDraft(BaseModel):
    id: str
    source_type: str  # manual, project, git, note, job
    topic: str
    hook: str
    body: str
    status: str = "DRAFT"  # DRAFT, READY, APPROVED, SCHEDULED, PUBLISHED, FAILED, CANCELLED
    approval_token: Optional[str] = None
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    post_urn: Optional[str] = None
    created_at: str

class MessageThread(BaseModel):
    thread_id: str
    participants: List[str]
    last_message: Optional[str] = None
    unread_count: int = 0
