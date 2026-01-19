import pytest
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_navigation_history():
    manager = BrowserManager()
    await manager.start()
    
    # 1. Navigate to first page
    await manager.navigate("https://example.com")
    title1 = await manager.page.title()
    assert "Example Domain" in title1
    
    # 2. Navigate to second page
    await manager.navigate("https://google.com")
    title2 = await manager.page.title()
    assert "Google" in title2
    
    # 3. Go back
    await manager.go_back()
    title_back = await manager.page.title()
    assert "Example Domain" in title_back
    
    # 4. Go forward
    await manager.go_forward()
    title_forward = await manager.page.title()
    assert "Google" in title_forward
    
    # 5. Reload
    # We can check if reload works by setting a variable on window and seeing it disappear?
    # Or just ensure it doesn't crash.
    await manager.reload()
    title_reload = await manager.page.title()
    assert "Google" in title_reload
    
    await manager.close()
