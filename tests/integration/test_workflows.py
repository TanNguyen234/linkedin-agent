"""Integration tests for high-level workflows and database."""
from src.core.storage.database import LocalDatabase
from src.core.config.settings import get_settings
from src.core.models.models import JobPosting, ProfileSnapshot
from src.intelligence.content.service import ContentService
from src.workflows.job_hunt import run_job_hunt_workflow

def test_job_hunt_workflow():
    profile = ProfileSnapshot(
        name="Alex Dev",
        headline="Agentic AI Engineer",
        about="Specialized in Python RAG systems.",
        skills=["Python", "LLM", "RAG"]
    )
    jobs = [
        JobPosting(id="1", title="AI Engineer", company="Nova", url="http://nova.ai", description="Python and LLM skills needed"),
        JobPosting(id="2", title="AI Engineer", company="Nova", url="http://nova.ai/dup", description="Duplicate listing"),
        JobPosting(id="3", title="Cook", company="Kitchen", url="http://cook.com", description="Cooking food")
    ]
    results = run_job_hunt_workflow(jobs, profile, min_score=40)
    assert len(results) == 1  # Deduplicated and non-relevant filtered
    assert results[0]["job"]["company"] == "Nova"
    assert "talking_points" in results[0]

def test_content_service_pipeline(tmp_path):
    db = LocalDatabase(db_path=str(tmp_path / "test.db"))
    svc = ContentService(db, get_settings())
    draft = svc.generate_draft("Autonomous Agents")
    assert draft.status == "DRAFT"
    
    preview = svc.preview_draft(draft.id)
    token = preview["approval_token"]
    
    pub_res = svc.publish_draft(draft.id, token)
    assert pub_res["status"] == "PUBLISHED"
