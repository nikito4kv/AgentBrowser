import pytest
from unittest.mock import AsyncMock
from agentbrowser.browser.manager import BrowserManager, SecurityRiskError


def _element_info(**overrides):
    info = {
        "success": True,
        "coordinates": [10, 10],
        "isOccluded": False,
        "occludedBy": None,
        "attributes": {"text": "Target", "ariaLabel": ""},
    }
    info.update(overrides)
    return info


@pytest.mark.asyncio
async def test_robust_click_occlusion():
    manager = BrowserManager()
    await manager.start()
    frame = manager.page.main_frame
    handle = frame.evaluate_handle.return_value
    frame.evaluate = AsyncMock(return_value=_element_info(isOccluded=True, occludedBy="Popup"))

    # Without force: refuse and tell the model what is in the way
    result = await manager.execute_action("left_click", ref="ref_1")
    assert "Action Failed" in result
    assert "occluded by 'Popup'" in result
    handle.click.assert_not_called()

    # With force: the occlusion check is skipped and the click is issued with force=True
    result_force = await manager.execute_action("left_click", ref="ref_1", force=True)
    assert result_force == "Clicked element ref_1"
    handle.click.assert_awaited_once_with(button="left", click_count=1, force=True)

    await manager.close()


@pytest.mark.asyncio
async def test_click_reports_missing_element():
    manager = BrowserManager()
    await manager.start()
    manager.page.main_frame.evaluate = AsyncMock(return_value={"success": False})

    result = await manager.execute_action("left_click", ref="ref_9")

    assert result == "Failed to find element ref: ref_9"
    manager.page.main_frame.evaluate_handle.return_value.click.assert_not_called()

    await manager.close()


@pytest.mark.asyncio
async def test_click_reports_playwright_failure():
    manager = BrowserManager()
    await manager.start()
    handle = manager.page.main_frame.evaluate_handle.return_value
    handle.click = AsyncMock(side_effect=RuntimeError("boom"))

    result = await manager.execute_action("left_click", ref="ref_1")

    assert result == "Click action failed on ref_1: boom"

    await manager.close()


@pytest.mark.asyncio
async def test_risky_click_requires_confirmation():
    """Elements whose text contains a risky keyword raise SecurityRiskError until forced."""
    manager = BrowserManager()
    await manager.start()
    manager.page.main_frame.evaluate = AsyncMock(
        return_value=_element_info(attributes={"text": "Delete account", "ariaLabel": ""})
    )
    handle = manager.page.main_frame.evaluate_handle.return_value

    with pytest.raises(SecurityRiskError) as exc:
        await manager.execute_action("left_click", ref="ref_1")
    assert "'delete'" in str(exc.value)
    assert "Delete account" in exc.value.risk_details
    handle.click.assert_not_called()

    result = await manager.execute_action("left_click", ref="ref_1", force=True)
    assert result == "Clicked element ref_1"
    handle.click.assert_awaited_once()

    await manager.close()
