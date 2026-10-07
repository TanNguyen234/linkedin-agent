"""Messaging service with approval gates."""
from typing import List, Dict, Any, Tuple
from ...core.models import MessageThread
from ...core.security import approvals
from ..browser.manager import BrowserManager

class MessagingService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    async def list_threads(self, limit: int = 20) -> List[MessageThread]:
        return [MessageThread(thread_id="thread-1", participants=["Lead Recruiter"], unread_count=0)]

    def prepare_message(self, recipient: str, message: str) -> Tuple[Dict[str, Any], str]:
        payload = {"recipient": recipient, "message": message}
        token = approvals.request_approval("send_message", payload)
        return payload, token

    async def send_message(self, recipient: str, message: str, approval_token: str) -> Dict[str, Any]:
        payload = {"recipient": recipient, "message": message}
        ok, reason = approvals.consume_approval(approval_token, "send_message", payload)
        if not ok:
            return {"status": "BLOCKED", "error": reason}
        return {"status": "SENT", "recipient": recipient}
