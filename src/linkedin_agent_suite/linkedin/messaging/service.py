"""Real messaging service interacting with LinkedIn DOM and gated by approval."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

from ...core.models import MessageThread
from ...core.security import approvals
from ..browser.manager import BrowserManager
from ..session.manager import SessionManager, SessionState

logger = logging.getLogger(__name__)

# Strict allowlist for LinkedIn URLs
ALLOWED_HOSTS = {"www.linkedin.com", "linkedin.com"}
VANITY_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]{2,100}$")


def validate_linkedin_recipient(recipient: str) -> str | None:
    """Validate and normalize recipient identifier or profile URL. Return normalized URL or None."""
    recipient = recipient.strip()
    if not recipient:
        return None

    if recipient.startswith("http://") or recipient.startswith("https://"):
        parsed = urlparse(recipient)
        if parsed.scheme != "https":
            return None
        if parsed.netloc.lower() not in ALLOWED_HOSTS:
            return None
        path = parsed.path.rstrip("/")
        if path.startswith("/in/") and len(path) > 4:
            return f"https://www.linkedin.com{path}/"
        if path.startswith("/messaging/thread/") and len(path) > 18:
            return f"https://www.linkedin.com{path}/"
        return None

    if VANITY_PATTERN.match(recipient):
        return f"https://www.linkedin.com/in/{recipient}/"

    return None


class MessagingService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    def prepare_message(
        self, recipient: str, message: str
    ) -> tuple[dict[str, Any], str]:
        normalized = validate_linkedin_recipient(recipient)
        target = normalized or recipient
        payload = {"recipient": target, "message": message}
        token = approvals.request_approval("send_message", payload)
        return payload, token

    async def list_threads(self, limit: int = 20) -> list[MessageThread]:
        """Extract real message conversations from LinkedIn messaging."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            await page.goto(
                "https://www.linkedin.com/messaging/",
                wait_until="domcontentloaded",
                timeout=25000,
            )
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                logger.warning("Session not authenticated for list_threads: %s", state)
                return []

            try:
                await page.wait_for_selector(
                    ".msg-conversations-container__conversations-list, .msg-conversation-listitem",
                    timeout=10000,
                )
            except Exception:
                return []

            items = await page.query_selector_all(".msg-conversation-listitem")
            threads: list[MessageThread] = []
            for item in items[:limit]:
                p_elem = await item.query_selector(
                    ".msg-conversation-listitem__participant-names, .artdeco-entity-lockup__title"
                )
                participants = (
                    [(await p_elem.inner_text()).strip()]
                    if p_elem
                    else []
                )

                s_elem = await item.query_selector(
                    ".msg-overlay-list-bubble__message-snippet, .msg-conversation-card__message-snippet"
                )
                snippet = (await s_elem.inner_text()).strip() if s_elem else ""

                u_elem = await item.query_selector(
                    ".msg-conversation-listitem__unread-count"
                )
                unread = int((await u_elem.inner_text()).strip()) if u_elem else 0

                link_elem = await item.query_selector("a[href*='/messaging/thread/']")
                href = await link_elem.get_attribute("href") if link_elem else None
                href_str = str(href or "")
                thread_id = (
                    href_str.split("/thread/")[1].split("/")[0].split("?")[0]
                    if "/thread/" in href_str
                    else ""
                )

                if thread_id:
                    threads.append(
                        MessageThread(
                            thread_id=thread_id,
                            participants=participants,
                            snippet=snippet,
                            unread_count=unread,
                            last_message=snippet,
                        )
                    )
            return threads
        finally:
            await page.close()

    async def get_thread_messages(
        self, thread_id: str, limit: int = 50
    ) -> list[dict[str, str]]:
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            await page.goto(
                f"https://www.linkedin.com/messaging/thread/{thread_id}/",
                wait_until="domcontentloaded",
                timeout=25000,
            )
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                return []

            try:
                await page.wait_for_selector(
                    ".msg-s-message-list__event, .msg-s-event-listitem", timeout=10000
                )
            except Exception:
                return []

            items = await page.query_selector_all(
                ".msg-s-message-list__event, .msg-s-event-listitem"
            )
            messages = []
            for item in items[-limit:]:
                sender_el = await item.query_selector(
                    ".msg-s-message-group__name, .msg-s-message-group__profile-link"
                )
                body_el = await item.query_selector(".msg-s-event-listitem__body")
                time_el = await item.query_selector("time")
                if body_el:
                    messages.append(
                        {
                            "sender": (await sender_el.inner_text()).strip()
                            if sender_el
                            else "",
                            "text": (await body_el.inner_text()).strip(),
                            "time": (await time_el.inner_text()).strip()
                            if time_el
                            else "",
                        }
                    )
            return messages
        finally:
            await page.close()

    async def send_message(
        self, recipient: str, message: str, approval_token: str
    ) -> dict[str, Any]:
        """Type and submit message only after valid approval consumption and verified recipient targeting."""
        target_url = validate_linkedin_recipient(recipient)
        if not target_url:
            return {
                "status": "BLOCKED",
                "error": f"Invalid recipient or untrusted URL: '{recipient}'. Must be a valid LinkedIn username or https://www.linkedin.com/in/... URL.",
            }

        # Validate exact approval payload
        payload = {"recipient": target_url, "message": message}
        # Fallback payload check for unnormalized recipient
        alt_payload = {"recipient": recipient, "message": message}
        ok, reason = approvals.consume_approval(approval_token, "send_message", payload)
        if not ok:
            ok, reason = approvals.consume_approval(approval_token, "send_message", alt_payload)
            if not ok:
                return {"status": "BLOCKED", "error": reason}

        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            # 1. Navigate to target profile or conversation
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                return {"status": "AUTH_REQUIRED", "error": f"Session state: {state.value}"}

            # 2. Click message button scoped to profile top card
            msg_btn = await page.query_selector(
                '.pv-top-card-v2-ctas button:has-text("Message"), main button:has-text("Message"), button[aria-label*="Message"]'
            )
            if not msg_btn:
                return {
                    "status": "RECIPIENT_NOT_FOUND",
                    "error": "No Message button found on target profile.",
                }
            await msg_btn.click()

            # 3. Wait for composer
            composer = await page.wait_for_selector(
                'div.msg-form__contenteditable, div[contenteditable="true"]',
                timeout=10000,
            )
            if not composer:
                return {"status": "FAILED", "error": "Message composer not found."}

            # Record prior outgoing message count in conversation to ensure new message confirmation
            prior_events = await page.query_selector_all(
                ".msg-s-message-list__event, .msg-s-event-listitem"
            )
            prior_count = len(prior_events)

            # Focus and type message
            await composer.click()
            await composer.fill(message)

            # 4. Submit message
            send_btn = await page.query_selector(
                'button.msg-form__send-button, button:has-text("Send")'
            )
            if not send_btn:
                return {"status": "FAILED", "error": "Send button not found."}

            is_disabled = await send_btn.get_attribute("disabled")
            if is_disabled:
                return {"status": "FAILED", "error": "Send button is disabled."}

            await send_btn.click()

            # 5. Authoritative outgoing message detection (polling up to 5s)
            confirmed = False
            for _ in range(10):
                await page.wait_for_timeout(500)
                new_events = await page.query_selector_all(
                    ".msg-s-message-list__event, .msg-s-event-listitem"
                )
                if len(new_events) > prior_count:
                    # Check the latest event content
                    latest_event = new_events[-1]
                    body_el = await latest_event.query_selector(".msg-s-event-listitem__body, p")
                    if body_el:
                        latest_text = (await body_el.inner_text()).strip()
                        if message.strip()[:30] in latest_text or latest_text in message:
                            confirmed = True
                            break
                    else:
                        confirmed = True
                        break

            if confirmed:
                return {"status": "SENT", "recipient": recipient, "confirmed": True}
            return {
                "status": "SEND_UNCONFIRMED",
                "recipient": recipient,
                "details": "Message submitted but new outgoing message DOM event was not observed within timeout.",
                "confirmed": False,
            }
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
        finally:
            await page.close()
