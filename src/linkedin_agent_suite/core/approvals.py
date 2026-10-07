"""Cryptographically bound, single-use approval gate."""
from __future__ import annotations

import hmac
import hashlib
import json
import time
from typing import Dict, Any, Tuple

_SECRET_KEY = b"linkedin-agent-suite-secure-salt-2026-v2"
_PENDING_APPROVALS: Dict[str, Dict[str, Any]] = {}

def canonical_payload_digest(action_type: str, payload: Dict[str, Any]) -> str:
    canonical = json.dumps({"action": action_type, "payload": payload}, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def request_approval(action_type: str, payload: Dict[str, Any], ttl_seconds: int = 600) -> str:
    digest = canonical_payload_digest(action_type, payload)
    raw = f"{digest}:{time.time()}"
    token = hmac.new(_SECRET_KEY, raw.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
    _PENDING_APPROVALS[token] = {
        "action_type": action_type,
        "digest": digest,
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
    
    current_digest = canonical_payload_digest(action_type, payload)
    if not hmac.compare_digest(record["digest"], current_digest):
        return False, "Approval payload mismatch: Token does not authorize this exact payload."
    
    # Consumed - single use
    del _PENDING_APPROVALS[token]
    return True, "Approval confirmed."
