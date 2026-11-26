import os
import pytest
from unittest.mock import AsyncMock
from agentbrowser.browser.manager import BrowserManager

HTML = os.path.join(os.path.dirname(__file__), "test_occlusion.html")


@pytest.mark.asyncio
async def test_occlusion_detection():
    """read_page -> click on a covered button: refused with the culprit named; force goes through."""
    manager = BrowserManager(headless=True)
    await manager.start()
    frame = manager.page.main_frame
    handle = frame.evaluate_handle.return_value

    # Frame answers like the real JS helpers do for tests/test_occlusion.html:
    # the DOM script returns the tree, the element script reports the covering overlay.
    async def evaluate_side_effect(script, *args):
        if "window.__generateAccessibilityTree" in script:
            return {"pageContent": '  - button "Target Button" [ref=ref_1] id="target-btn"'}
        return {
            "success": True,
            "coordinates": [150, 125],
            "isOccluded": True,
            "occludedBy": "div#overlay",
            "attributes": {"text": "Target Button", "ariaLabel": ""},
        }

    frame.evaluate = AsyncMock(side_effect=evaluate_side_effect)

    try:
        await manager.execute_action("navigate", text=f"file://{os.path.abspath(HTML)}")
        manager.page.goto.assert_awaited_once()
        assert manager.page.goto.await_args.args[0].endswith("test_occlusion.html")

        tree = await manager.execute_action("read_page")
        target_ref = "ref_1"
        assert target_ref in tree

        # Normal click is refused with the name of the covering element; nothing is clicked
        result = await manager.execute_action("left_click", ref=target_ref)
        assert "Action Failed" in result
        assert "occluded by 'div#overlay'" in result
        handle.click.assert_not_called()

        # Forced click skips the check and reaches Playwright with force=True
        result_force = await manager.execute_action("left_click", ref=target_ref, force=True)
        assert "Clicked element ref_1" in result_force
        assert "Action Failed" not in result_force
        handle.click.assert_awaited_once_with(button="left", click_count=1, force=True)
    finally:
        await manager.close()
