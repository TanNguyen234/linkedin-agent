"""Real connection request service interacting with LinkedIn DOM and gated by approval."""

from __future__ import annotations

import logging
from typing import Any

from ...core.security import approvals
from ..browser.manager import BrowserManager
from ..session.manager import SessionManager, SessionState

logger = logging.getLogger(__name__)


class ConnectionService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    def prepare_connection_request(
        self, identifier: str, note: str | None = None
    ) -> tuple[dict[str, Any], str]:
        payload = {"identifier": identifier, "note": note or ""}
        token = approvals.request_approval("connect", payload)
        return payload, token

    async def get_status(self, identifier: str) -> str:
        """Check connection status with identifier."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            url = (
                f"https://www.linkedin.com/in/{identifier}/"
                if not identifier.startswith("http")
                else identifier
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                return f"UNKNOWN ({state})"

            if await page.query_selector('button:has-text("Pending")'):
                return "PENDING"
            if await page.query_selector(
                'button:has-text("1st"), span:has-text("1st degree")'
            ):
                return "CONNECTED"
            if await page.query_selector(
                'button:has-text("Connect"), button[aria-label*="Connect"]'
            ):
                return "CONNECTABLE"
            return "UNKNOWN"
        finally:
            await page.close()

    async def send_connection_request(
        self, identifier: str, note: str | None = None, approval_token: str = ""
    ) -> dict[str, Any]:
        """Perform real connection request after approval consumption."""
        payload = {"identifier": identifier, "note": note or ""}
        ok, reason = approvals.consume_approval(approval_token, "connect", payload)
        if not ok:
            return {"status": "BLOCKED", "error": reason}

        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            url = (
                f"https://www.linkedin.com/in/{identifier}/"
                if not identifier.startswith("http")
                else identifier
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                return {"status": "AUTH_REQUIRED", "error": f"Session state: {state}"}

            # Check if already connected or pending
            if await page.query_selector('button:has-text("Pending")'):
                return {"status": "ALREADY_PENDING", "identifier": identifier}
            if await page.query_selector('span:has-text("1st degree")'):
                return {"status": "ALREADY_CONNECTED", "identifier": identifier}

            # Locate connect button
            connect_btn = await page.query_selector(
                'button:has-text("Connect"), button[aria-label*="Connect"]'
            )
            if not connect_btn:
                # Check "More" dropdown
                more_btn = await page.query_selector(
                    'button[aria-label="More actions"], button:has-text("More")'
                )
                if more_btn:
                    await more_btn.click()
                    await page.wait_for_timeout(500)
                    connect_btn = await page.query_selector(
                        '.artdeco-dropdown__content button:has-text("Connect")'
                    )

            if not connect_btn:
                return {
                    "status": "FAILED",
                    "error": "Connect button not available for this member.",
                }

            await connect_btn.click()
            await page.wait_for_timeout(1000)

            # Handle Note Dialog
            if note:
                add_note_btn = await page.query_selector(
                    'button[aria-label="Add a note"], button:has-text("Add a note")'
                )
                if add_note_btn:
                    await add_note_btn.click()
                    textarea = await page.wait_for_selector(
                        'textarea[name="message"]', timeout=5000
                    )
                    if textarea:
                        await textarea.fill(note[:300])
                    send_invite_btn = await page.query_selector(
                        'button[aria-label="Send invitation"], button:has-text("Send")'
                    )
                    if send_invite_btn:
                        await send_invite_btn.click()
                else:
                    # Note not allowed, send without note
                    send_btn = await page.query_selector(
                        'button[aria-label="Send without a note"], button:has-text("Send")'
                    )
                    if send_btn:
                        await send_btn.click()
            else:
                send_btn = await page.query_selector(
                    'button[aria-label="Send without a note"], button:has-text("Send without a note"), button:has-text("Send")'
                )
                if send_btn:
                    await send_btn.click()

            await page.wait_for_timeout(2000)

            # Verify pending status
            pending = await page.query_selector('button:has-text("Pending")')
            if pending:
                return {"status": "REQUESTED", "identifier": identifier}
            return {
                "status": "UNCONFIRMED",
                "identifier": identifier,
                "details": "Request sent, pending confirmation not observed.",
            }
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
        finally:
            await page.close()
