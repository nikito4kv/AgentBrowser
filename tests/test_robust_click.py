import pytest
import os
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_robust_click_success():
    manager = BrowserManager()
    await manager.start()
    
    file_path = "file://" + os.path.abspath("tests/test_overlap.html")
    await manager.navigate(file_path)
    
    await manager.capture_annotated_screenshot()
    
    # Assuming ID 1 is the button
    # In the current implementation, this should FAIL (timeout or interception)
    # We want it to SUCCEED eventually.
    
    # We'll use a short timeout in the implementation logic later to speed up retries.
    # For now, let's just call click_element.
    
    # To avoid waiting 30s during the 'Red' phase run, we can't easily change the default timeout 
    # without changing the code.
    
    # So, I will write the test to expect success.
    # When I run it now, it will likely timeout (fail).
    
    try:
        result = await manager.click_element(1)
    except Exception:
        result = False
        
    # If the feature is NOT implemented, result might be True (if playwright forces it? no, standard doesn't)
    # or it raises Exception.
    
    # Verification:
    text = await manager.page.inner_text("#target-btn")
    
    await manager.close()
    
    assert text == "Clicked"