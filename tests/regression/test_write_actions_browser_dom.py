"""DOM regression tests for write actions using real Chromium browser and DOM fixtures."""

import pytest

from linkedin_agent_suite.core.security import approvals
from linkedin_agent_suite.linkedin.browser.manager import BrowserManager
from linkedin_agent_suite.linkedin.connections.service import ConnectionService
from linkedin_agent_suite.linkedin.messaging.service import MessagingService


@pytest.mark.asyncio
async def test_messaging_untrusted_url_blocked(tmp_path):
    browser = BrowserManager(user_data_dir=tmp_path / "browser")
    service = MessagingService(browser)

    payload = {"recipient": "http://evil.com/phish", "message": "hello"}
    token = approvals.request_approval("send_message", payload)

    res = await service.send_message("http://evil.com/phish", "hello", token)
    assert res["status"] == "BLOCKED"
    assert "Invalid recipient or untrusted URL" in res["error"]


@pytest.mark.asyncio
async def test_connection_untrusted_url_blocked(tmp_path):
    browser = BrowserManager(user_data_dir=tmp_path / "browser")
    service = ConnectionService(browser)

    payload = {"identifier": "https://attacker.org/in/victim", "note": "Hi"}
    token = approvals.request_approval("connect", payload)

    res = await service.send_connection_request(
        "https://attacker.org/in/victim", "Hi", token
    )
    assert res["status"] == "BLOCKED"
    assert "Invalid profile target" in res["error"]


@pytest.mark.asyncio
async def test_connection_already_connected_dom_detection(tmp_path, monkeypatch):
    profile_dir = tmp_path / "browser_conn"
    browser = BrowserManager(user_data_dir=profile_dir, headless=True)
    service = ConnectionService(browser)

    # Mock page navigation to load an already-connected DOM
    fixture_html = """
    <!DOCTYPE html>
    <html>
    <body>
        <div class="global-nav"></div>
        <div class="pv-top-card-v2-ctas">
            <span class="dist-value">1st degree</span>
            <button>Message</button>
        </div>
    </body>
    </html>
    """

    async def mock_goto(self, url, **kwargs):
        await self.set_content(fixture_html)

    from patchright.async_api import Page

    monkeypatch.setattr(Page, "goto", mock_goto)

    payload = {
        "identifier": "https://www.linkedin.com/in/connected-user/",
        "note": "Connect",
    }
    token = approvals.request_approval("connect", payload)

    res = await service.send_connection_request(
        "https://www.linkedin.com/in/connected-user/", "Connect", token
    )
    assert res["status"] == "ALREADY_CONNECTED"
    await browser.close()


@pytest.mark.asyncio
async def test_connection_note_unavailable_blocks_invitation(tmp_path, monkeypatch):
    """When a note is requested in approval but modal has no note button, it must BLOCK instead of silently sending."""
    profile_dir = tmp_path / "browser_note_blocked"
    browser = BrowserManager(user_data_dir=profile_dir, headless=True)
    service = ConnectionService(browser)

    fixture_html = """
    <!DOCTYPE html>
    <html>
    <body>
        <div class="global-nav"></div>
        <div class="pv-top-card-v2-ctas">
            <button>Connect</button>
        </div>
        <!-- Modal without Add a note button -->
        <div class="artdeco-modal">
            <button aria-label="Send without a note">Send without a note</button>
        </div>
    </body>
    </html>
    """

    async def mock_goto(self, url, **kwargs):
        await self.set_content(fixture_html)

    from patchright.async_api import Page

    monkeypatch.setattr(Page, "goto", mock_goto)

    payload = {
        "identifier": "https://www.linkedin.com/in/target-user/",
        "note": "Important note that must not be lost",
    }
    token = approvals.request_approval("connect", payload)

    res = await service.send_connection_request(
        "https://www.linkedin.com/in/target-user/",
        "Important note that must not be lost",
        token,
    )
    assert res["status"] == "BLOCKED"
    assert "NOTE_UNAVAILABLE" in res["error"]
    await browser.close()
