import pytest
from agentbrowser.browser.manager import BrowserManager
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_screenshot_method():
    manager = BrowserManager()
    await manager.start()
    
    # Test direct capture
    result = await manager.capture_screenshot()
    
    manager.page.screenshot.assert_called()
    assert result == b"fake_screenshot"
    
    await manager.close()

@pytest.mark.asyncio
async def test_screenshot_action_tool():
    manager = BrowserManager()
    await manager.start()
    
    # Test the tool action (which acts as a no-op/refresh signal)
    result = await manager.execute_action("screenshot")
    
    assert result == "Screenshot taken (visual state refreshed)"
    
    await manager.close()