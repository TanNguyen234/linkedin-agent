# SOURCE MAP & CODE REUSABILITY CLASSIFICATION
**Project:** LinkedIn Agent Suite  
**Generated:** October 7, 2026 (Phase 3)

---

## 1. Upstream to Merged Architecture Mapping

This document maps all key files and modules from the two reference repositories to their target architectural modules in `linkedin-agent-suite`.

| Component / Feature | Upstream Module (Source) | Classification | Destination in `linkedin-agent-suite` | Rationale & Changes |
| :--- | :--- | :--- | :--- | :--- |
| **Browser Management** | `stickerdaniel/linkedin_mcp_server/core/browser.py`, `drivers/browser.py` | REUSABLE AFTER REFACTORING | `src/linkedin/browser/manager.py` | Strip FastMCP Context. Retain Patchright browser launch, viewport settings, and clean process exit fences. |
| **Session & Cookie Import** | `stickerdaniel/linkedin_mcp_server/core/auth.py`, `browser_import/` | REUSABLE AFTER REFACTORING | `src/linkedin/session/manager.py`, `src/linkedin/session/cookie_importer.py` | Retain DPAPI Windows cookie decryption from Chrome, Edge, Brave. Replace FastMCP auth errors with clean domain exceptions. |
| **Person & Profile Extraction** | `stickerdaniel/linkedin_mcp_server/linkedin/person.py`, `profile_page.py` | REUSABLE AFTER REFACTORING | `src/linkedin/profiles/service.py` | Extract DOM selectors for Experience, Education, Skills, About. Return typed `LinkedInProfile` Pydantic model. |
| **Company Extraction** | `stickerdaniel/linkedin_mcp_server/linkedin/company.py` | REUSABLE AFTER REFACTORING | `src/linkedin/companies/service.py` | Extract company overview, employees, and company posts. Strip MCP tool decorators. |
| **LinkedIn Job Search** | `stickerdaniel/linkedin_mcp_server/linkedin/jobs.py`, `job_pages.py` | REUSABLE AFTER REFACTORING | `src/linkedin/jobs/service.py` | Cleanly wraps LinkedIn job search queries, description extraction, and apply URL parsing. |
| **Messaging & Inbox** | `stickerdaniel/linkedin_mcp_server/linkedin/conversations.py`, `message_sender.py` | REUSABLE AFTER REFACTORING | `src/linkedin/messaging/service.py` | Wrap thread listing and reading. Place `send_message` strictly behind `ApprovalGate`. |
| **Connection Actions** | `stickerdaniel/linkedin_mcp_server/linkedin/connection.py`, `connection_actions.py` | REUSABLE AFTER REFACTORING | `src/linkedin/connections/service.py` | Check connection status; send invite with note behind `ApprovalGate`. |
| **Feed & Post Search** | `stickerdaniel/linkedin_mcp_server/linkedin/feed.py`, `posts.py` | REUSABLE AFTER REFACTORING | `src/linkedin/feed/service.py` | Read home feed updates; search posts by keyword. |
| **Profile Audit Engine** | `jcnh74/src/tools/auditProfile.ts` | REWRITE (TypeScript -> Python) | `src/intelligence/profile/audit.py` | Deterministic 5-dimension scoring engine (Searchability, Clarity, Credibility, AI Positioning, Conversion). |
| **Keywords & Coverage** | `jcnh74/src/keywords.ts` | REWRITE (TypeScript -> Python) | `src/intelligence/profile/keywords.py` | Curated role keyword banks, stop words, regex bi-gram extractor from job descriptions. |
| **Profile Section Rewriter** | `jcnh74/src/tools/generateHeadlineVariants.ts`, `rewriteAbout.ts`, `rewriteExperience.ts` | REWRITE (TypeScript -> Python) | `src/intelligence/profile/generator.py` | Multi-variant headline and About section templates. Zero invented metrics. |
| **Public Remote Job Scrapers** | `jcnh74/src/jobs/jobSources.ts` | REWRITE (TypeScript -> Python) | `src/intelligence/job_matching/public_sources.py` | Async HTTP client fetching Remotive & RemoteOK public jobs. |
| **Job Fit Ranker** | `jcnh74/src/tools/rankJobFit.ts` | REWRITE (TypeScript -> Python) | `src/intelligence/job_matching/ranker.py` | 0-100 fit scoring combining keyword overlap and title affinity. |
| **Application Prep & Tracker** | `jcnh74/src/tools/prepareApplication.ts`, `trackApplications.ts`, `jobStore.ts` | REWRITE (TypeScript -> Python) | `src/intelligence/application/prep.py`, `src/core/storage/tracker.py` | Talking points, cover note generator, and local SQLite application tracker. |
| **Official Post Publisher** | `jcnh74/src/linkedin/officialApiClient.ts`, `src/tools/createLinkedInPost.ts` | REWRITE (TypeScript -> Python) | `src/intelligence/content/publishing/official.py` | Calls LinkedIn REST API v2 (`/rest/posts`) using `httpx`. Strict 2-step approval. |
| **Automatic Content Engine** | *User Specification* | NEW ENGINE | `src/intelligence/content/` | Full pipeline: Milestone extractor from Git diffs, topic planner, hook generator, humanizer, validator, voice profile, calendar, duplicate guard. |
| **High-Level Workflows** | *User Specification* | NEW ORCHESTRATION | `src/workflows/` | `job_hunt.py`, `networking.py`, `profile_optimizer.py`, `content_pipeline.py`. |
| **CLI Suite** | `stickerdaniel/cli_main.py` & jcnh74 scripts | REWRITE / UNIFIED | `src/cli/` | Rich Typer CLI with `doctor`, `profile`, `jobs`, `inbox`, `networking`, `post`, `applications`. |

---

## 2. Upstream Code Quality & Risk Evaluation

### 2.1 Reusable Directly / After Refactoring
- `stickerdaniel` DOM extraction logic in `linkedin/*.py` is battle-tested against live LinkedIn DOM structures and includes defensive checks for missing elements.
- `jcnh74` scoring algorithms and keyword banks are robust, clean, and mathematically sound.

### 2.2 Tightly Coupled to MCP (To Be Stripped)
- `stickerdaniel/linkedin_mcp_server/server.py` and `tools/*.py`: Heavy FastMCP decorators and context objects. Replaced with pure Python service methods.
- `jcnh74/src/index.ts`: `@modelcontextprotocol/sdk` tool declarations.

### 2.3 Dangerous / Dropped Upstream Code
- `stickerdaniel/daemon_election.py` & `daemon_lock.py`: Over-engineered 1,500+ lines of distributed election logic across local processes that frequently causes deadlocks on Windows. Dropped in favor of a standard single-process lock file.
- Unofficial browser profile editing: Neither repo supports automated profile editing via browser (due to aggressive bot detection and account restrictions). Kept manual via drafted patches.
