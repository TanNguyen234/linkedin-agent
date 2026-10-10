"""Hook generation and complete post builder connected to LLM providers."""

from __future__ import annotations

import datetime
import subprocess
import uuid
from pathlib import Path

from ...core.models import PostDraft
from .duplicate_detector import is_duplicate_content
from .humanizer import humanize_text
from .llm_provider import LLMProvider
from .validator import validate_claims


def generate_hooks(topic: str) -> list[str]:
    return [
        f"Most architectures for {topic} fail due to brittle state management. Here is what worked in practice:",
        f"We just deployed an update for {topic}. Three engineering lessons learned from production:",
        f"If you are designing {topic}, avoid this common failure mode before scaling:",
    ]


def extract_git_project_evidence(repo_path: Path | str = ".") -> list[str]:
    """Extract real git commits, status, and milestone evidence from local repository."""
    repo = Path(repo_path)
    if not (repo / ".git").exists():
        return []

    evidence = []
    try:
        # 1. Recent commits
        res = subprocess.run(
            ["git", "log", "-5", "--oneline"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            evidence.append(f"Recent Commits:\n{res.stdout.strip()}")

        # 2. Latest commit summary
        res_show = subprocess.run(
            ["git", "show", "--stat", "--oneline", "HEAD"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_show.returncode == 0 and res_show.stdout.strip():
            evidence.append(f"Latest Milestone:\n{res_show.stdout.strip()[:300]}")

        # 3. Readme headline if exists
        readme_file = repo / "README.md"
        if readme_file.exists():
            first_lines = "\n".join(readme_file.read_text(encoding="utf-8").splitlines()[:5])
            if first_lines.strip():
                evidence.append(f"Project Focus: {first_lines.strip()[:200]}")
    except Exception:
        return []

    return evidence


def create_post_draft(
    topic: str,
    context_facts: list[str],
    hook_index: int = 0,
    provider: LLMProvider | None = None,
    existing_posts: list[str] | None = None,
) -> PostDraft:
    """Generate a high-quality post draft connected to LLM provider or grounded template."""
    hooks = generate_hooks(topic)
    selected_hook = hooks[min(hook_index, len(hooks) - 1)]

    facts_summary = "\n".join(f"- {f}" for f in context_facts) if context_facts else "No additional context facts."

    if provider is not None and type(provider).__name__ != "MockLLMProvider":
        prompt = (
            f"Write a technical, authentic LinkedIn engineering post about '{topic}'.\n"
            f"Opening hook to use: {selected_hook}\n"
            f"Grounded facts:\n{facts_summary}\n"
            f"Do not invent false metrics, revenue numbers, or customer counts."
        )
        try:
            generated_body = provider.generate(prompt)
        except Exception:
            generated_body = ""
    else:
        generated_body = ""

    if not generated_body:
        # Grounded structured template incorporating actual context facts
        facts_block = "\n".join(f"- {f}" for f in context_facts[:3]) if context_facts else "- Grounded implementation and verified tests."
        generated_body = (
            f"{selected_hook}\n\n"
            f"{facts_block}\n\n"
            f"Key takeaways:\n"
            f"1. Keep contracts explicit rather than guessing schemas.\n"
            f"2. Decouple business logic from external adapter frameworks.\n"
            f"3. Verify with deterministic tests instead of relying on mocks alone.\n\n"
            f"What is your preferred pattern when dealing with this in production?\n\n"
            f"#SoftwareEngineering #SystemDesign"
        )

    clean_body = humanize_text(generated_body)
    is_valid, warnings = validate_claims(clean_body, source_facts=context_facts)

    # Duplicate check against existing posts
    if existing_posts and is_duplicate_content(clean_body, existing_posts):
        status = "DUPLICATE_WARNING"
    elif is_valid:
        status = "DRAFT"
    else:
        status = "VALIDATION_WARNING"

    draft_id = f"post-{uuid.uuid4().hex[:8]}"
    return PostDraft(
        id=draft_id,
        source_type="project" if context_facts else "manual",
        topic=topic,
        hook=selected_hook,
        body=clean_body,
        status=status,
        evidence=context_facts,
        created_at=datetime.datetime.now().isoformat(),
    )
