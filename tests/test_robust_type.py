import pytest
from unittest.mock import AsyncMock
from agentbrowser.browser.manager import BrowserManager


@pytest.mark.asyncio
async def test_robust_type_success():
    manager = BrowserManager()
    await manager.start()

    result = await manager.execute_action("type", text="Robust Input", ref="ref_1")

    handle = manager.page.main_frame.evaluate_handle.return_value
    handle.type.assert_awaited_once_with("Robust Input", delay=50)
    assert "Typed: Robust Input into ref_1" in result

    await manager.close()


@pytest.mark.asyncio
async def test_robust_type_force_is_passed_to_focus_click():
    manager = BrowserManager()
    await manager.start()

    await manager.execute_action("type", text="x", ref="ref_1", force=True)

    handle = manager.page.main_frame.evaluate_handle.return_value
    handle.click.assert_awaited_once_with(click_count=3, force=True)

    await manager.close()


@pytest.mark.asyncio
async def test_robust_type_reports_blocked_field():
    """If the focus click is intercepted (e.g. by an overlay) the error is returned, nothing is typed."""
    manager = BrowserManager()
    await manager.start()
    handle = manager.page.main_frame.evaluate_handle.return_value
    handle.click = AsyncMock(side_effect=RuntimeError("<div id=overlay> intercepts pointer events"))

    result = await manager.execute_action("type", text="blocked", ref="ref_1")

    assert result.startswith("Type failed on ref_1:")
    assert "intercepts pointer events" in result
    handle.type.assert_not_called()
    manager.page.keyboard.press.assert_not_called()

    await manager.close()
