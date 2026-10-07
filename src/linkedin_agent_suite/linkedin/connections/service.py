"""Connections service with approval gates."""
from typing import Dict, Any, Tuple
from ...core.security import approvals
from ..browser.manager import BrowserManager

class ConnectionService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    def prepare_connection_request(self, profile_id: str, note: str = "") -> Tuple[Dict[str, Any], str]:
        payload = {"profile_id": profile_id, "note": note}
        token = approvals.request_approval("connect_person", payload)
        return payload, token

    async def send_connection_request(self, profile_id: str, note: str, approval_token: str) -> Dict[str, Any]:
        payload = {"profile_id": profile_id, "note": note}
        ok, reason = approvals.consume_approval(approval_token, "connect_person", payload)
        if not ok:
            return {"status": "BLOCKED", "error": reason}
        return {"status": "REQUESTED", "profile_id": profile_id}
