# LINKEDIN AGENT SUITE — UNIFIED MERGE & ARCHITECTURE PLAN
**Project:** LinkedIn Agent Suite (`D:/Download/linkedin-agent-suite`)  
**Phase:** Phase 1 — Architecture Plan  
**Status:** Approved for Implementation

---

## 1. System Vision & Architecture

The **LinkedIn Agent Suite** is a unified, standalone, production-ready LinkedIn automation, profile optimization, job hunting, and content generation system.

It bridges the deep browser-level execution of `stickerdaniel/linkedin-mcp-server` with the local-first analytical intelligence and official publishing of `jcnh74/linkedin-profile-manager-mcp`, augmented with an **Automatic LinkedIn Content Engine**.

### 1.1 Core Principles
1. **Zero Mandatory MCP Runtime:** The core business and domain services are pure, standalone Python modules with zero dependency on MCP servers. MCP is purely an optional outer adapter.
2. **Unified Browser & Session Stack:** Exactly one browser manager (`Patchright`/Chromium), one session store (`~/.linkedin-agent-suite/session/`), and automatic cookie importation from existing everyday browsers (Chrome, Edge, Brave, etc.) via DPAPI/Keychain.
3. **Deterministic Intelligence & No Fabricated Metrics:** Profile scoring, keyword coverage, and job fit ranking run locally and deterministically. Never invent numbers, metrics, or career milestones.
4. **Safety & Two-Step Approval Gates:** All write actions (sending messages, sending connection requests, publishing posts) are gated behind explicit human preview and confirmation tokens.
5. **Multi-Channel Publishing:** Prefer official LinkedIn API (`/rest/posts`) when credentials exist; fallback to browser publisher only with explicit human consent.

---

## 2. Target Directory & Module Structure

```text
linkedin-agent-suite/
├── src/
│   ├── core/
│   │   ├── config/              # Central Pydantic settings & .env loader
│   │   ├── logging/             # Structured JSON/console logging
│   │   ├── storage/             # SQLite & JSON local persistence (jobs, tracker, posts)
│   │   ├── errors/              # Domain exception hierarchy
│   │   ├── models/              # Unified data schemas (Profile, Job, Post, Thread)
│   │   └── security/            # Token generation, rate-limits & confirmation gates
│   │
│   ├── linkedin/                # Browser Action & Extraction Layer (stickerdaniel refined)
│   │   ├── browser/             # Unified BrowserManager (Patchright launch, viewport, pool)
│   │   ├── session/             # SessionManager (cookie import from Chrome/Edge, login check)
│   │   ├── profiles/            # Profile reader (experience, skills, about, education)
│   │   ├── people/              # People search with facet filters
│   │   ├── companies/           # Company info, employee search, company posts
│   │   ├── feed/                # Home feed extractor & post search
│   │   ├── jobs/                # LinkedIn job search, job details, apply URL parsing
│   │   ├── messaging/           # Inbox listing, conversation threads, message sender
│   │   └── connections/         # Connection status & send connection request with note
│   │
│   ├── intelligence/            # Analytical & Content Engines (jcnh74 ported & enhanced)
│   │   ├── profile/             # Profile audit (5 dimensions), keyword gap, patch exporter
│   │   ├── job_matching/        # Job normalizer, public sources (Remotive/RemoteOK), fit ranker
│   │   ├── application/         # Talking points generator, cover note, application tracker
│   │   └── content/             # AUTOMATIC CONTENT ENGINE
│   │       ├── topic_selector.py     # Milestone extraction from Git/notes/projects
│   │       ├── post_generator.py     # Hook generation (3 variants), body builder
│   │       ├── humanizer.py          # Anti-AI cliché filtering, cadence variation
│   │       ├── validator.py          # Claim & fact validation against source facts
│   │       ├── voice_profile.py      # Style learning & persona matching
│   │       ├── calendar.py           # Editorial schedule & slot allocator
│   │       ├── spam_detector.py      # Duplicate & semantic saturation guard
│   │       └── publishing/           # Official REST API & Browser publishers
│   │
│   ├── workflows/               # High-Level Orchestrations
│   │   ├── job_hunt.py          # search -> deduplicate -> rank -> prepare
│   │   ├── networking.py        # search people -> inspect -> draft outreach
│   │   ├── profile_optimizer.py # audit -> keyword gap -> headline/about variants -> patch
│   │   └── content_pipeline.py  # source -> plan -> draft -> humanize -> validate -> publish
│   │
│   ├── cli/                     # CLI Interface (Rich / Click / Typer)
│   │   ├── main.py              # CLI entry point (`linkedin-agent`)
│   │   ├── commands_profile.py
│   │   ├── commands_jobs.py
│   │   ├── commands_network.py
│   │   ├── commands_inbox.py
│   │   └── commands_post.py
│   │
│   └── adapters/                # Optional Interfaces
│       └── mcp/                 # Optional thin FastMCP wrapper
│
├── tests/
│   ├── unit/                    # Fast isolated tests for parsers, scoring, schemas
│   ├── integration/             # Component tests (storage, config, pipeline)
│   ├── regression/              # Upstream bug regression test cases
│   └── live/                    # Read-only and approval-gated live tests
├── scripts/                     # Standalone helper scripts
├── docs/                        # Architecture, reports & user manuals
├── data/                        # Local SQLite databases, drafts, profile snapshots
├── logs/                        # Structured execution logs
├── .env.example
├── pyproject.toml
└── README.md
```

---

## 3. Detailed Component Architecture

### 3.1 Core Layer (`src/core/`)
- **`config/`**: Reads `settings.json`, `.env`, and environment variables. Strictly rejects passwords/plain tokens in config files.
- **`storage/`**: Local SQLite storage engine for:
  - Job cache & history
  - Job application tracker
  - Post drafts, schedules, and publishing history
  - Profile snapshots
- **`security/`**: Approval token generator using HMAC-SHA256 (`request_approval`, `consume_approval`), preventing unauthorized write actions.

### 3.2 LinkedIn Browser Layer (`src/linkedin/`)
- Unified `BrowserManager`: Uses `patchright` async Chromium with persistent context at `data/browser_profile`.
- `SessionManager`:
  - Scans installed Chrome, Brave, Edge, and Opera profiles on Windows (via DPAPI decryptor).
  - Validates session by hitting `https://www.linkedin.com/feed/` checking for active login indicators.
  - Graceful fallback: If no session exists, prompts user to sign in manually via headed window without CAPTCHA circumvention.
- Services: Expose clean async methods returning typed Pydantic models (e.g., `LinkedInProfile`, `LinkedInJob`, `MessageThread`).

### 3.3 Intelligence Layer (`src/intelligence/`)
- **Profile Auditor**: Port of `auditProfile.ts` to Python:
  - Recruiter Searchability (0-100)
  - Clarity (0-100)
  - Credibility / Metrics Density (0-100)
  - AI / Engineering Positioning (0-100)
  - Conversion / CTA (0-100)
- **Job Ranker**:
  - Combined pool: LinkedIn live search jobs + public remote jobs (Remotive, RemoteOK).
  - Deduplication: Title + Company normalization.
  - Scoring: Keyword overlap against profile + title affinity heuristics.
- **Application Prep & Tracker**:
  - Generates talking points strictly anchored in candidate's real experience bullets.
  - Drafts cover notes and records application status in local tracker (`SAVED`, `APPLIED`, `INTERVIEWING`, `OFFER`, `REJECTED`).

### 3.4 Automatic Content Engine (`src/intelligence/content/`)
- **Topic Selection & Milestone Extraction**:
  - `from_project(path)`: Scans git log, recent commit messages, README, architecture changes to detect true technical milestones (MVP release, benchmark win, bugfix).
  - `from_note(path)`: Extracts insights from technical markdown/text notes.
  - `from_job_learning(job_id)`: Transforms interview/job requirements into industry insights.
- **Multi-Hook Generation**: Generates 3 contrasting hook styles (Contrarian/Direct/Story), evaluates against voice profile, and selects the strongest.
- **Humanizer Engine**:
  - Cleans out generic AI tokens ("Delve", "In today's fast-paced world", "Game changer", "Tapestry", excessive rocket emojis).
  - Regulates sentence length variance (burstiness).
- **Claim & Fact Validator**: Cross-checks generated claims against input facts. Flag any unverified quantitative claim.
- **Voice Profile**: Learns style parameters from user's historical approved posts stored in `data/profile/voice.json`.
- **Publishing Layer**:
  - `OfficialLinkedInPublisher`: Uses `httpx` to call LinkedIn REST API `/rest/posts` when `LINKEDIN_ACCESS_TOKEN` is present.
  - `BrowserPublisher`: Fallback browser posting with mandatory human verification.
  - Modes: `APPROVAL` (default), `SCHEDULED`, `AUTONOMOUS` (disabled by default, with strict daily caps).

---

## 4. Phase-by-Phase Execution Roadmap

1. **Phase 2 — Upstream Download:** Clone `stickerdaniel/linkedin-mcp-server` and `jcnh74/linkedin-profile-manager-mcp` to `D:/Download/`. Record commit hashes in `UPSTREAM_VERSIONS.md`.
2. **Phase 3 — Deep Local Source Analysis:** Inspect local codebases, verify internal interfaces, generate `SOURCE_MAP.md`.
3. **Phase 4 — Decouple MCP:** Build core services without any MCP decorators or dependencies.
4. **Phase 5 — Unify Browser & Session:** Implement `BrowserManager` & `SessionManager` in `src/linkedin/browser/` and `src/linkedin/session/`.
5. **Phase 6 — Merge Capabilities & Content Engine:** Implement all profile, job, networking, and content generation pipelines.
6. **Phase 7 & 8 — Configuration & Observability:** Setup Pydantic settings, structured logging to `logs/agent.log`.
7. **Phase 9 — Multi-Layer Testing:** Run static checks, unit tests, mock integration tests, and regression tests.
8. **Phase 10 — Test Report:** Document all test outcomes in `TEST_REPORT.md`.
9. **Phase 11 — Live Read-Only Test:** Safely verify read-only operations with live LinkedIn session.
10. **Phase 12 — Live Write Gate:** Write operations (message, connect, post) gated with explicit human confirmation.
11. **Phase 13 & 14 — Hardening & CLI:** Provide rich CLI command suite (`linkedin-agent`).
12. **Phase 15 & 16 — Documentation & Final Audit:** Complete all architecture docs, verify clean state.

---

## 5. Architectural Approval Verdict

**APPROVED.** The architecture satisfies all user constraints, integrates both repositories cleanly into a single Python system, eliminates runtime MCP coupling, and integrates the complete Content Engine specification.
