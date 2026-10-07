"""Cryptographically bound, single-use approval gate."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

_PENDING_APPROVALS: dict[str, dict[str, Any]] = {}
_CACHED_SECRET: bytes | None = None


def get_approval_secret_key() -> bytes:
    global _CACHED_SECRET
    if _CACHED_SECRET is not None:
        return _CACHED_SECRET

    env_secret = os.environ.get("APPROVAL_HMAC_SECRET")
    if env_secret:
        _CACHED_SECRET = env_secret.encode("utf-8")
        return _CACHED_SECRET

    key_path = Path("data/secrets/approval.key")
    if key_path.exists():
        try:
            _CACHED_SECRET = key_path.read_bytes().strip()
            if _CACHED_SECRET:
                return _CACHED_SECRET
        except Exception:
            pass

    new_secret = secrets.token_bytes(32)
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(new_secret)
        try:
            os.chmod(key_path, 0o600)
        except Exception:
            pass
    except Exception:
        pass

    _CACHED_SECRET = new_secret
    return _CACHED_SECRET


def canonical_payload_digest(action_type: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        {"action": action_type, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def request_approval(
    action_type: str, payload: dict[str, Any], ttl_seconds: int = 600
) -> str:
    digest = canonical_payload_digest(action_type, payload)
    raw = f"{digest}:{time.time()}:{secrets.token_hex(8)}"
    secret = get_approval_secret_key()
    token = hmac.new(secret, raw.encode("utf-8"), hashlib.sha256).hexdigest()[:24]
    _PENDING_APPROVALS[token] = {
        "action_type": action_type,
        "digest": digest,
        "payload": payload,
        "expires_at": time.time() + ttl_seconds,
    }
    return token


def consume_approval(
    token: str, action_type: str, payload: dict[str, Any]
) -> tuple[bool, str]:
    if not token or token not in _PENDING_APPROVALS:
        return False, "Invalid or unrecognized approval token."

    record = _PENDING_APPROVALS[token]
    if time.time() > record["expires_at"]:
        del _PENDING_APPROVALS[token]
        return False, "Approval token has expired."

    current_digest = canonical_payload_digest(action_type, payload)
    if not hmac.compare_digest(record["digest"], current_digest):
        return (
            False,
            "Approval payload mismatch: Token does not authorize this exact payload.",
        )

    if record["action_type"] != action_type:
        return (
            False,
            f"Approval action mismatch: Token authorizes {record['action_type']}, not {action_type}.",
        )

    del _PENDING_APPROVALS[token]
    return True, "Approval confirmed."
