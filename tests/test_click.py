import pytest
from agentbrowser.browser.manager import BrowserManager
from conftest import make_frame


@pytest.mark.asyncio
async def test_click_action():
    """A ref click resolves the element handle in the main frame and clicks through it."""
    manager = BrowserManager()
    await manager.start()

    result = await manager.execute_action("left_click", ref="ref_1")

    frame = manager.page.main_frame
    frame.evaluate_handle.assert_awaited_with("window.__claudeElementMap['ref_1'].deref()")
    handle = frame.evaluate_handle.return_value
    handle.click.assert_awaited_once_with(button="left", click_count=1, force=False)
    # A ref click never falls back to raw mouse coordinates
    manager.page.mouse.click.assert_not_called()
    assert result == "Clicked element ref_1"

    await manager.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("action, button, count", [
    ("right_click", "right", 1),
    ("double_click", "left", 2),
])
async def test_click_variants(action, button, count):
    manager = BrowserManager()
    await manager.start()

    await manager.execute_action(action, ref="ref_1")

    handle = manager.page.main_frame.evaluate_handle.return_value
    handle.click.assert_awaited_once_with(button=button, click_count=count, force=False)

    await manager.close()


@pytest.mark.asyncio
async def test_click_by_coordinate_uses_mouse():
    manager = BrowserManager()
    await manager.start()

    result = await manager.execute_action("left_click", coordinate=[120, 340])

    manager.page.mouse.click.assert_awaited_once_with(120, 340, button="left", click_count=1)
    assert result == "Clicked at 120, 340"

    await manager.close()


@pytest.mark.asyncio
async def test_click_resolves_ref_in_child_frame():
    """`frame{i}_ref_N` must be resolved in page.frames[i], not in the main frame."""
    manager = BrowserManager()
    await manager.start()

    child = make_frame("https://child.example.test/")
    manager.page.frames = [manager.page.main_frame, child]

    result = await manager.execute_action("left_click", ref="frame1_ref_3")

    child.evaluate_handle.assert_awaited_with("window.__claudeElementMap['frame1_ref_3'].deref()")
    child.evaluate_handle.return_value.click.assert_awaited_once()
    manager.page.main_frame.evaluate_handle.assert_not_called()
    assert result == "Clicked element frame1_ref_3"

    await manager.close()
