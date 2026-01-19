import pytest
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_browser_manager_lifecycle():
    manager = BrowserManager()
    await manager.start()
    assert manager.browser is not None
    assert manager.page is not None
    
    await manager.navigate("https://example.com")
    title = await manager.page.title()
    assert "Example Domain" in title
    
    await manager.close()
    assert manager.browser is None
