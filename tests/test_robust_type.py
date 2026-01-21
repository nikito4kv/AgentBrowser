import pytest
import os
from agentbrowser.browser.manager import BrowserManager
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_robust_type_success():
    manager = BrowserManager()
    await manager.start()
    
    # Default mock returns success=True, not occluded
    result = await manager.execute_action("type", text="Robust Input", ref="ref_1")
    
    manager.page.keyboard.type.assert_called()
    assert "Typed: Robust Input" in result
    
    await manager.close()