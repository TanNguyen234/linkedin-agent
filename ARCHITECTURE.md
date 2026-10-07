# System Architecture

## Architecture Overview
```text
LinkedIn Agent Suite
├── src/core/            # Config, SQLite Database, HMAC Approvals, Models, Errors
├── src/linkedin/        # BrowserManager, SessionManager, Profile/Job/Message extractors
├── src/intelligence/    # Profile Audit, Job Ranker, Application Prep, Content Engine
├── src/workflows/       # High-level orchestrations (Job Hunt, Networking, Content Pipeline)
└── src/cli/             # Typer CLI (`doctor`, `profile-audit`, `post-create`, etc.)
```

## Key Invariants
1. Zero MCP coupling in core logic.
2. Single browser stack with persistent profile directory.
3. No fabricated metrics or hallucinations in profile and content generation.
4. Two-phase approval tokens (`request_approval` -> `consume_approval`) required for write actions.
