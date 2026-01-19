import pytest
import os
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_robust_type_success():
    manager = BrowserManager()
    await manager.start()
    
    file_path = "file://" + os.path.abspath("tests/test_overlap_type.html")
    await manager.navigate(file_path)
    await manager.capture_annotated_screenshot()
    
    # Assuming ID 1 is the input
    test_text = "Robust Input"
    success = await manager.type_text(1, test_text)
    
    value = await manager.page.input_value("#target-input")
    await manager.close()
    
    assert value == test_text
