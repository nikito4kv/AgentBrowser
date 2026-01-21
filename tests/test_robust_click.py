import pytest
import os
from agentbrowser.browser.manager import BrowserManager
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_robust_click_occlusion():
    manager = BrowserManager()
    await manager.start()
    
    # Override evaluate to return occlusion
    manager.page.evaluate = AsyncMock(return_value={
        "success": True, 
        "coordinates": [10, 10], 
        "isOccluded": True, 
        "occludedBy": "Popup"
    })
    
    # Try clicking without force
    result = await manager.execute_action("left_click", ref="ref_1")
    
    # Should fail
    assert "Action Failed" in result
    assert "occluded by 'Popup'" in result
    
    # Try clicking WITH force
    result_force = await manager.execute_action("left_click", ref="ref_1", force=True)
    
    # Should succeed (manager calls click anyway)
    manager.page.mouse.click.assert_called()
    assert "Clicked element ref_1" in result_force
    
    await manager.close()
