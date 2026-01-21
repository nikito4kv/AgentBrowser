import pytest
import os
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_click_action():
    manager = BrowserManager()
    await manager.start()
    
    # Executing click
    result = await manager.execute_action("left_click", ref="ref_1")
    
    # Verify mouse.click was called
    # The default mock returns coordinates [10, 10]
    manager.page.mouse.click.assert_called_with(10, 10, button="left", click_count=1)
    assert "Clicked element ref_1" in result
    
    await manager.close()