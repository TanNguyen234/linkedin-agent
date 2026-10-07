"""Regression test to prevent duplicate core packages from returning."""
from pathlib import Path

def test_no_duplicate_core_folders():
    src_dir = Path("src")
    root_core = src_dir / "core"
    assert not root_core.exists(), "Duplicate src/core directory must not exist! Canonical is src/linkedin_agent_suite/core"
    
    canonical_core = src_dir / "linkedin_agent_suite" / "core"
    assert canonical_core.exists(), "Canonical src/linkedin_agent_suite/core must exist"
