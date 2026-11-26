import pytest
from agentbrowser.browser.manager import BrowserManager


@pytest.mark.asyncio
async def test_type_action():
    """Typing into a ref: focus by triple click, clear with Backspace, then type with a delay."""
    manager = BrowserManager()
    await manager.start()

    result = await manager.execute_action("type", text="Hello", ref="ref_1")

    handle = manager.page.main_frame.evaluate_handle.return_value
    handle.click.assert_awaited_once_with(click_count=3, force=False)
    manager.page.keyboard.press.assert_awaited_once_with("Backspace")
    handle.type.assert_awaited_once_with("Hello", delay=50)
    assert result == "Typed: Hello into ref_1"

    await manager.close()


@pytest.mark.asyncio
async def test_type_without_ref_types_blind():
    manager = BrowserManager()
    await manager.start()

    result = await manager.execute_action("type", text="Hello")

    manager.page.keyboard.type.assert_awaited_once_with("Hello", delay=50)
    assert result == "Typed: Hello"

    await manager.close()
