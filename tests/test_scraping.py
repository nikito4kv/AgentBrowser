import pytest
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_read_page():
    manager = BrowserManager()
    await manager.start()
    
    # Mock return value is set in conftest.py
    # mock_page.evaluate = AsyncMock(return_value={"success": True, "coordinates": [10, 10], "pageContent": "<html></html>"})
    
    result = await manager.execute_action("read_page")
    
    # The default mock returns "<html></html>" as pageContent
    assert result == "<html></html>"
    
    await manager.close()