# LinkedIn Agent Suite

A standalone, production-ready LinkedIn Agent combining browser actions, profile intelligence, job hunting, and an automatic content engine.

## Features
- **Browser Actions**: Inspect profiles, companies, jobs, feed, and manage conversations.
- **Profile Intelligence**: 5-dimension deterministic audit (Recruiter searchability, Clarity, Credibility/Metrics, AI positioning, Conversion).
- **Job Match & Prep**: Deduplication, keyword-gap analysis, 0-100 fit ranking, tailored talking points and cover notes.
- **Automatic Content Engine**: Milestone extraction from Git/notes, 3-hook generation, humanizer, anti-hallucination fact validator, and editorial calendar.
- **Zero Mandatory MCP Runtime**: All business logic runs natively via CLI and scripts.
- **Safety First**: HMAC two-phase approval tokens for write and publish actions.

## Quickstart
```bash
# Install dependencies
pip install -e .

# Run system diagnostic
python -m src.cli.main doctor

# Audit your profile
python -m src.cli.main profile-audit

# Generate a technical post draft
python -m src.cli.main post-create --topic "Multi-Agent Orchestration"
```
