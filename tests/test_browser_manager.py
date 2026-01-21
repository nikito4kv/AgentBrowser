import pytest
from agentbrowser.browser.manager import BrowserManager
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_browser_manager_lifecycle():
    manager = BrowserManager()
    await manager.start()
    assert manager.browser is not None
    assert manager.page is not None
    
    # Mock title for the page
    manager.page.title = AsyncMock(return_value="Example Domain")
    
    await manager.execute_action("navigate", text="https://example.com")
    manager.page.goto.assert_called()
    
    title = await manager.page.title()
    assert "Example Domain" in title
    
    await manager.close()
    # Check if close was called on context
    manager.context.close.assert_called()