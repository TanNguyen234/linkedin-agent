"""Real messaging service interacting with LinkedIn DOM and gated by approval."""

from __future__ import annotations

import logging
from typing import Any

from ...core.models import MessageThread
from ...core.security import approvals
from ..browser.manager import BrowserManager
from ..session.manager import SessionManager, SessionState

logger = logging.getLogger(__name__)


class MessagingService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    def prepare_message(
        self, recipient: str, message: str
    ) -> tuple[dict[str, Any], str]:
        payload = {"recipient": recipient, "message": message}
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
                logger.warning(f"Session not authenticated for list_threads: {state}")
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
                # Extract participant names
                p_elem = await item.query_selector(
                    ".msg-conversation-listitem__participant-names, .artdeco-entity-lockup__title"
                )
                participants = (
                    [(await p_elem.inner_text()).strip()]
                    if p_elem
                    else ["LinkedIn Member"]
                )

                # Extract last message snippet
                s_elem = await item.query_selector(
                    ".msg-overlay-list-bubble__message-snippet, .msg-conversation-card__message-snippet"
                )
                snippet = (await s_elem.inner_text()).strip() if s_elem else ""

                # Extract unread count
                u_elem = await item.query_selector(
                    ".msg-conversation-listitem__unread-count"
                )
                unread = int((await u_elem.inner_text()).strip()) if u_elem else 0

                # Extract thread id
                link_elem = await item.query_selector("a[href*='/messaging/thread/']")
                href = await link_elem.get_attribute("href") if link_elem else None
                href_str = str(href or "")
                thread_id = (
                    href_str.split("/messaging/thread/")[1].split("/")[0]
                    if "/messaging/thread/" in href_str
                    else f"t-{len(threads) + 1}"
                )

                threads.append(
                    MessageThread(
                        thread_id=thread_id,
                        participants=participants,
                        unread_count=unread,
                        snippet=snippet,
                    )
                )
            return threads
        finally:
            await page.close()

    async def read_thread(self, thread_id: str) -> list[dict[str, Any]]:
        """Read message events inside a specific thread."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            url = (
                f"https://www.linkedin.com/messaging/thread/{thread_id}/"
                if not thread_id.startswith("http")
                else thread_id
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                return [{"error": f"Authentication state required: {state}"}]

            try:
                await page.wait_for_selector(
                    ".msg-s-message-list__event, .msg-s-event-listitem", timeout=10000
                )
            except Exception:
                return []

            events = await page.query_selector_all(
                ".msg-s-message-list__event, .msg-s-event-listitem"
            )
            messages: list[dict[str, Any]] = []
            for ev in events:
                sender_el = await ev.query_selector(
                    ".msg-s-message-group__name, .msg-s-message-group__profile-link"
                )
                body_el = await ev.query_selector(".msg-s-event-listitem__body")
                time_el = await ev.query_selector("time")
                if body_el:
                    messages.append(
                        {
                            "sender": (await sender_el.inner_text()).strip()
                            if sender_el
                            else "Unknown",
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
        """Type and submit message only after valid approval consumption."""
        payload = {"recipient": recipient, "message": message}
        ok, reason = approvals.consume_approval(approval_token, "send_message", payload)
        if not ok:
            return {"status": "BLOCKED", "error": reason}

        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            # 1. Navigate to messaging composer or recipient profile
            target_url = (
                f"https://www.linkedin.com/in/{recipient}/"
                if not recipient.startswith("http")
                and not recipient.startswith("thread-")
                else recipient
            )
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                return {"status": "AUTH_REQUIRED", "error": f"Session state: {state}"}

            # 2. Click message button on profile
            msg_btn = await page.query_selector(
                'button:has-text("Message"), button[aria-label*="Message"]'
            )
            if not msg_btn:
                return {
                    "status": "RECIPIENT_NOT_FOUND",
                    "error": "No Message button found on profile.",
                }
            await msg_btn.click()

            # 3. Wait for composer
            composer = await page.wait_for_selector(
                'div.msg-form__contenteditable, div[contenteditable="true"]',
                timeout=10000,
            )
            if not composer:
                return {"status": "FAILED", "error": "Message composer not found."}

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
            await page.wait_for_timeout(2000)

            # 5. Verify sent status in conversation
            # Verify the message text appears in the conversation
            sent_bubble = await page.query_selector(f'text="{message[:25]}"')
            if sent_bubble:
                return {"status": "SENT", "recipient": recipient}
            return {
                "status": "SEND_UNCONFIRMED",
                "recipient": recipient,
                "details": "Message submitted but DOM confirmation timed out.",
            }
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
        finally:
            await page.close()
