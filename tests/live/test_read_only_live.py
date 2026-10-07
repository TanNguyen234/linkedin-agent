"""Read-only live LinkedIn tests gated by explicit environment variable."""

import os

import pytest


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_LINKEDIN_TESTS") != "1",
    reason="Live tests require RUN_LIVE_LINKEDIN_TESTS=1",
)
def test_read_only_live_session():
    # Only runs when authorized explicitly
    pass
