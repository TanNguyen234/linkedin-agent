"""Extract milestones from Git or notes strictly with evidence."""
import os
import subprocess
from typing import Dict, Any

def extract_from_git(repo_path: str) -> Dict[str, Any]:
    try:
        cmd = ["git", "-C", repo_path, "log", "-n", "3", "--pretty=format:%s"]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        commits = [line.strip() for line in out.splitlines() if line.strip()]
        if not commits:
            return {"status": "NO_EVIDENCE", "error": "Git log returned empty commit history"}
        return {
            "status": "VALID_EVIDENCE",
            "topic": f"Technical Update: {os.path.basename(repo_path)}",
            "milestone": commits[0],
            "evidence": commits
        }
    except Exception as e:
        return {"status": "NO_EVIDENCE", "error": f"Failed to read git repository: {e}"}
