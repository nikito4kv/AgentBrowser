import pytest
import os
from agentbrowser.browser.manager import BrowserManager
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_type_action():
    manager = BrowserManager()
    await manager.start()
    
    # Executing type
    # We use a ref 'ref_1'
    # The default mock in conftest returns success=True for element lookup
    result = await manager.execute_action("type", text="Hello", ref="ref_1")
    
    # Verify type was called
    manager.page.keyboard.type.assert_called_with("Hello", delay=50)
    assert "Typed: Hello" in result
    
    await manager.close()