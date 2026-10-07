"""Profile section rewrite generators."""
from typing import List, Dict, Any
from src.core.models.models import ProfileSnapshot

def generate_headline_variants(profile: ProfileSnapshot) -> List[Dict[str, str]]:
    return [
        {
            "role": "Agentic AI Systems Engineer",
            "headline": "Agentic AI Systems Engineer | LLMs, Multi-Agent Orchestration & RAG | Python & TypeScript",
            "rationale": "High recruiter keyword density for AI/agentic roles."
        },
        {
            "role": "Senior Full Stack & AI Engineer",
            "headline": "Senior Full Stack & AI Engineer | Building Scalable Agentic Systems & Production RAG | Fast, Pragmatic Delivery",
            "rationale": "Balances full-stack engineering rigor with modern AI capabilities."
        },
        {
            "role": "AI Automation Consultant",
            "headline": "AI Automation Architect | Transforming Workflows with Autonomous Agents & LLM Integration",
            "rationale": "Client-facing, ROI-focused positioning."
        }
    ]

def rewrite_about(profile: ProfileSnapshot, style: str = "ai-forward") -> str:
    return (
        "I am an engineer focused on building robust, production-grade agentic AI systems and scalable architectures.\n\n"
        "My work centers on turning advanced LLM capabilities into deterministic software: multi-agent workflows, "
        "hybrid retrieval (RAG), and resilient backend services. I prioritize clean code, test-driven validation, and measurable impact.\n\n"
        "Core Stack: Python, TypeScript, LangChain/LlamaIndex, Vector Databases, FastMCP/APIs, Docker.\n\n"
        "Open to challenging AI Engineering opportunities and high-impact technical collaborations. Feel free to reach out via DM or email."
    )
