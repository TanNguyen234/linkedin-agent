# Acceptance Capability Matrix

| Feature | Source File | Implementation Status | Unit Evidence | Integration Evidence | Regression / Contract Evidence | Live Evidence | Remaining Issue | Commit |
|---|---|---|---|---|---|---|---|---|
| Official Posting Contract & Settings | `core/config.py`, `content/service.py` | IMPLEMENTED | `test_disabled_posting_blocked`, `test_missing_token_blocked` | `test_content_service_end_to_end_publish_flow` | `test_publish_missing_post_urn_returns_unconfirmed` | LIVE NOT RUN | None | Current |
| Identity Resolution & URN Validation | `publishing/official.py` | IMPLEMENTED | `test_invalid_author_urn_format`, `test_valid_author_urn_configured` | `test_author_resolution_via_v2_me` | `test_oidc_userinfo_pairwise_rejected` | LIVE NOT RUN | Requires valid user token for live /v2/me | Current |
| API Versioning & Status Handling | `publishing/official.py` | IMPLEMENTED | `test_publish_api_version_expired_426` | `test_publish_rate_limit_429` | `test_publish_timeout_returns_unconfirmed`, `test_publish_server_error_500` | LIVE NOT RUN | Default set to 202609 | Current |
| Duplicate Publishing Guard | `content/service.py` | IMPLEMENTED | `test_content_service_end_to_end_publish_flow` | `test_content_service_end_to_end_publish_flow` | None | LIVE NOT RUN | None | Current |
| Application Schema Migration | `core/storage/migrations.py` | IMPLEMENTED | None | `test_database_and_content_service` | Schema version 3 | N/A | None | Current |
