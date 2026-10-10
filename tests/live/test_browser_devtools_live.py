"""Live browser test with Chrome DevTools Protocol (CDP) inspection."""

import logging

import pytest

from linkedin_agent_suite.linkedin.browser.manager import BrowserManager
from linkedin_agent_suite.linkedin.session.manager import SessionManager, SessionState

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_live_browser_with_chrome_devtools(tmp_path):
    """Exercise real Chromium with Chrome DevTools Protocol attached."""
    profile_dir = tmp_path / "browser_devtools_profile"
    manager = BrowserManager(user_data_dir=profile_dir, headless=True)

    try:
        context = await manager.start()
        assert context is not None, "Browser context must launch successfully"

        page = await manager.get_page()
        assert page is not None

        # 1. Attach Chrome DevTools Protocol (CDP) session
        cdp = await context.new_cdp_session(page)
        assert cdp is not None, "CDP session must be established"

        # 2. Enable Chrome DevTools domains
        await cdp.send("Page.enable")
        await cdp.send("Network.enable")
        await cdp.send("Console.enable")
        await cdp.send("Runtime.enable")
        await cdp.send("DOM.enable")

        console_messages = []
        network_requests = []

        cdp.on("Console.messageAdded", lambda e: console_messages.append(e))
        cdp.on("Network.requestWillBeSent", lambda e: network_requests.append(e))

        # 3. Navigate to a test page with active DOM and JS
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>LinkedIn Agent Suite DevTools Live Test</title></head>
        <body>
            <div id="app">
                <header class="global-nav">
                    <h1>LinkedIn Agent Suite Console Diagnostic</h1>
                </header>
                <main class="feed-shared-update-v2">
                    <p class="content">Live test verifying real browser execution, DOM nodes, and DevTools telemetry.</p>
                </main>
            </div>
            <script>
                console.log("[DevTools Live Test] Script executed successfully in page context.");
                window.__AGENT_SUITE_READY = true;
            </script>
        </body>
        </html>
        """
        await page.set_content(html_content)

        # 4. Use Chrome DevTools Protocol Runtime.evaluate
        eval_res = await cdp.send(
            "Runtime.evaluate",
            {"expression": "window.__AGENT_SUITE_READY", "returnByValue": True},
        )
        assert eval_res.get("result", {}).get("value") is True, (
            "DevTools Runtime.evaluate must confirm window.__AGENT_SUITE_READY"
        )

        # 5. Use Chrome DevTools Protocol DOM.getDocument to inspect DOM tree
        dom_tree = await cdp.send("DOM.getDocument", {"depth": 3})
        assert "root" in dom_tree, "DevTools DOM domain must return document root"
        root_node_name = dom_tree["root"].get("nodeName")
        assert root_node_name == "#document", f"Expected #document, got {root_node_name}"

        # 6. Verify SessionManager detector with live authenticated signal (.global-nav)
        session_mgr = SessionManager(manager)
        state_auth = await session_mgr.detect_session_state(page)
        assert state_auth == SessionState.AUTHENTICATED, (
            f"Expected AUTHENTICATED when .global-nav present, got {state_auth}"
        )

        # 7. Test unauthenticated login page detection
        login_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <form action="/login-submit">
                <input id="username" type="text" />
                <input id="password" type="password" />
            </form>
        </body>
        </html>
        """
        await page.set_content(login_html)
        state_login = await session_mgr.detect_session_state(page)
        assert state_login == SessionState.LOGIN_REQUIRED, (
            f"Expected LOGIN_REQUIRED when login inputs present, got {state_login}"
        )

        # 8. Test security checkpoint detection
        checkpoint_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <div id="captcha-internal">Verify your identity</div>
        </body>
        </html>
        """
        await page.set_content(checkpoint_html)
        state_cp = await session_mgr.detect_session_state(page)
        assert state_cp == SessionState.CHECKPOINT, (
            f"Expected CHECKPOINT when captcha-internal present, got {state_cp}"
        )

        # 9. Capture screenshot to verify rendering pipeline
        screenshot_path = tmp_path / "devtools_live_test.png"
        await page.screenshot(path=str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0, "Screenshot file must contain rendered bytes"

        print(
            f"\n[PASS] Chrome DevTools Live Test Verified: DOM={root_node_name}, "
            f"State(Auth)={state_auth.value}, State(Login)={state_login.value}, "
            f"State(Checkpoint)={state_cp.value}, Screenshot={screenshot_path.stat().st_size} bytes"
        )

    finally:
        await manager.close()
