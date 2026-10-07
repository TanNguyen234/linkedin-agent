"""Integration tests for high-level workflows and database."""
from linkedin_agent_suite.core.storage.database import LocalDatabase
from linkedin_agent_suite.core.config import get_settings
from linkedin_agent_suite.core.models import Job, Profile
from linkedin_agent_suite.intelligence.content.service import ContentService
from linkedin_agent_suite.workflows.job_hunt import run_job_hunt_workflow

def test_job_hunt_workflow():
    profile = Profile(
        full_name="Alex Dev",
        headline="Agentic AI Engineer",
        about="Specialized in Python RAG systems.",
        skills=["Python", "LLM", "RAG"]
    )
    jobs = [
        Job(id="1", title="AI Engineer", company="Nova", url="http://nova.ai", description="Python and LLM skills needed"),
        Job(id="2", title="AI Engineer", company="Nova", url="http://nova.ai/dup", description="Duplicate listing"),
        Job(id="3", title="Cook", company="Kitchen", url="http://cook.com", description="Cooking food")
    ]
    results = run_job_hunt_workflow(jobs, profile, min_score=40)
    assert len(results) == 1
    assert results[0]["job"]["company"] == "Nova"

def test_database_and_content_service(tmp_path):
    settings = get_settings()
    db = LocalDatabase(db_path=str(tmp_path / "test.db"))
    svc = ContentService(db, settings)
    draft = svc.generate_draft("Autonomous Agents")
    assert draft.status == "DRAFT"
