import pytest
from unittest.mock import AsyncMock
from agentbrowser.browser.manager import BrowserManager
from conftest import make_frame


@pytest.mark.asyncio
async def test_read_page():
    manager = BrowserManager()
    await manager.start()

    # conftest: the main frame returns {"pageContent": "<html></html>", ...}
    result = await manager.execute_action("read_page")

    assert result == "=== Main Content ===\n<html></html>"
    # The tree is built by the DOM script with the interactive filter and the plain `ref` prefix
    script = manager.page.main_frame.evaluate.await_args.args[0]
    assert "window.__generateAccessibilityTree" in script
    assert '"filter": "interactive"' in script
    assert '"prefix": "ref"' in script

    await manager.close()


@pytest.mark.asyncio
async def test_read_page_includes_iframes_with_prefixed_refs():
    manager = BrowserManager()
    await manager.start()

    child = make_frame("https://ads.example.test/frame")
    child.evaluate = AsyncMock(return_value={"pageContent": '- button "Inner" [ref=frame1_ref_1]'})
    manager.page.frames = [manager.page.main_frame, child]

    result = await manager.execute_action("read_page")

    assert result.startswith("=== Main Content ===")
    assert "=== Iframe (https://ads.example.test/frame) ===" in result
    assert "frame1_ref_1" in result
    assert '"prefix": "frame1_ref"' in child.evaluate.await_args.args[0]

    await manager.close()


@pytest.mark.asyncio
async def test_read_page_skips_broken_frames_and_reports_empty():
    manager = BrowserManager()
    await manager.start()
    manager.page.main_frame.evaluate = AsyncMock(side_effect=RuntimeError("detached"))

    result = await manager.execute_action("read_page")

    assert result == "No content found."

    await manager.close()
