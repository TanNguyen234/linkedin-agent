"""Two-step HMAC approval gate for write/publish actions."""
import hmac
import hashlib
import time
from typing import Dict, Any, Tuple

_SECRET_KEY = b"linkedin-suite-secure-salt-2026"
_PENDING_APPROVALS: Dict[str, Dict[str, Any]] = {}

def request_approval(action_type: str, payload: Dict[str, Any], ttl_seconds: int = 600) -> str:
    raw = f"{action_type}:{str(sorted(payload.items()))}:{time.time()}"
    token = hmac.new(_SECRET_KEY, raw.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    _PENDING_APPROVALS[token] = {
        "action_type": action_type,
        "payload": payload,
        "expires_at": time.time() + ttl_seconds
    }
    return token

def consume_approval(token: str, action_type: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
    if not token or token not in _PENDING_APPROVALS:
        return False, "Invalid or missing approval token. Generate a preview first."
    
    record = _PENDING_APPROVALS[token]
    if time.time() > record["expires_at"]:
        del _PENDING_APPROVALS[token]
        return False, "Approval token has expired."
    
    if record["action_type"] != action_type:
        return False, "Action type mismatch."
    
    # Clean up token
    del _PENDING_APPROVALS[token]
    return True, "Approval confirmed."
