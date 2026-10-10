"""Real connection invitation service interacting with LinkedIn DOM and gated by approval."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

from ...core.security import approvals
from ..browser.manager import BrowserManager
from ..session.manager import SessionManager, SessionState

logger = logging.getLogger(__name__)

ALLOWED_HOSTS = {"www.linkedin.com", "linkedin.com"}
VANITY_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]{2,100}$")


def validate_linkedin_profile_target(identifier: str) -> str | None:
    """Validate and normalize LinkedIn profile URL or identifier."""
    identifier = identifier.strip()
    if not identifier:
        return None

    if identifier.startswith("http://") or identifier.startswith("https://"):
        parsed = urlparse(identifier)
        if parsed.scheme != "https":
            return None
        if parsed.netloc.lower() not in ALLOWED_HOSTS:
            return None
        path = parsed.path.rstrip("/")
        if path.startswith("/in/") and len(path) > 4:
            return f"https://www.linkedin.com{path}/"
        return None

    if VANITY_PATTERN.match(identifier):
        return f"https://www.linkedin.com/in/{identifier}/"

    return None


class ConnectionService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    def prepare_connection_request(
        self, identifier: str, note: str = ""
    ) -> tuple[dict[str, Any], str]:
        target_url = validate_linkedin_profile_target(identifier) or identifier
        payload = {"identifier": target_url, "note": note}
        token = approvals.request_approval("connect", payload)
        return payload, token

    async def send_connection_request(
        self, identifier: str, note: str, approval_token: str
    ) -> dict[str, Any]:
        """Send connection request only after valid approval consumption and verified targeting."""
        target_url = validate_linkedin_profile_target(identifier)
        if not target_url:
            return {
                "status": "BLOCKED",
                "error": f"Invalid profile target or untrusted URL: '{identifier}'. Must be a valid LinkedIn username or https://www.linkedin.com/in/... URL.",
            }

        # Check payload binding
        payload = {"identifier": target_url, "note": note}
        alt_payload = {"identifier": identifier, "note": note}
        ok, reason = approvals.consume_approval(approval_token, "connect", payload)
        if not ok:
            ok, reason = approvals.consume_approval(approval_token, "connect", alt_payload)
            if not ok:
                return {"status": "BLOCKED", "error": reason}

        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                return {"status": "AUTH_REQUIRED", "error": f"Session state: {state.value}"}

            # 1. Distinguish current connection status
            pending_el = await page.query_selector(
                'button:has-text("Pending"), .pv-top-card-v2-ctas button:has-text("Pending")'
            )
            if pending_el:
                return {"status": "ALREADY_PENDING", "identifier": identifier}

            first_degree_el = await page.query_selector(
                'span:has-text("1st degree"), span:has-text("1st"), .dist-value:has-text("1st")'
            )
            if first_degree_el:
                return {"status": "ALREADY_CONNECTED", "identifier": identifier}

            # 2. Locate connect button in profile hero card
            connect_btn = await page.query_selector(
                '.pv-top-card-v2-ctas button:has-text("Connect"), main button:has-text("Connect"), button[aria-label*="Invite"], button[aria-label*="Connect"]'
            )
            if not connect_btn:
                # Check "More" dropdown
                more_btn = await page.query_selector(
                    '.pv-top-card-v2-ctas button[aria-label*="More"], button[aria-label="More actions"], button:has-text("More")'
                )
                if more_btn:
                    await more_btn.click()
                    await page.wait_for_timeout(500)
                    connect_btn = await page.query_selector(
                        '.artdeco-dropdown__content button:has-text("Connect"), div[role="menu"] button:has-text("Connect")'
                    )

            if not connect_btn:
                # Check if only Follow is available
                follow_btn = await page.query_selector('button:has-text("Follow")')
                if follow_btn:
                    return {
                        "status": "FOLLOW_ONLY",
                        "error": "Connect button unavailable; profile only offers Follow.",
                    }
                return {
                    "status": "INVITATION_UNAVAILABLE",
                    "error": "Connect button not available on this profile.",
                }

            await connect_btn.click()
            await page.wait_for_timeout(1000)

            # 3. Handle Note Dialog strictly
            if note:
                add_note_btn = await page.query_selector(
                    'button[aria-label="Add a note"], button:has-text("Add a note")'
                )
                if not add_note_btn:
                    # BLOCK: Never silently drop the note if it was requested in approval
                    return {
                        "status": "BLOCKED",
                        "error": "NOTE_UNAVAILABLE: Connection note requested in approval payload, but LinkedIn modal did not provide 'Add a note'. Refusing to send bare request without note.",
                    }

                await add_note_btn.click()
                textarea = await page.wait_for_selector(
                    'textarea[name="message"], textarea#custom-message', timeout=5000
                )
                if not textarea:
                    return {
                        "status": "FAILED",
                        "error": "Note textarea not found in invitation modal.",
                    }

                await textarea.fill(note[:300])
                send_invite_btn = await page.query_selector(
                    'button[aria-label="Send invitation"], button:has-text("Send")'
                )
                if not send_invite_btn:
                    return {"status": "FAILED", "error": "Send invitation button not found."}
                await send_invite_btn.click()
            else:
                send_btn = await page.query_selector(
                    'button[aria-label="Send without a note"], button:has-text("Send without a note"), button:has-text("Send")'
                )
                if send_btn:
                    await send_btn.click()

            # 4. Authoritative verification of Pending status
            confirmed = False
            for _ in range(8):
                await page.wait_for_timeout(500)
                pending = await page.query_selector(
                    'button:has-text("Pending"), .pv-top-card-v2-ctas button:has-text("Pending")'
                )
                if pending:
                    confirmed = True
                    break

            if confirmed:
                return {"status": "REQUESTED", "identifier": identifier, "confirmed": True}
            return {
                "status": "UNCONFIRMED",
                "identifier": identifier,
                "details": "Invitation submitted, but Pending status was not observed in profile DOM within timeout.",
                "confirmed": False,
            }
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
        finally:
            await page.close()
