import pytest
import os
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_scroll_action():
    manager = BrowserManager()
    await manager.start()
    
    # Executing scroll
    await manager.execute_action("scroll", scroll_direction="down")
    
    # Verify mouse.wheel was called
    # Access the mock from manager.page (which is a mock)
    manager.page.mouse.wheel.assert_called()
    
    await manager.execute_action("scroll", scroll_direction="up")
    manager.page.mouse.wheel.assert_called()
    
    await manager.close()