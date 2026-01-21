import pytest
import os
import asyncio
from agentbrowser.browser.manager import BrowserManager
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_occlusion_detection():
    # Setup
    manager = BrowserManager(headless=True)
    await manager.start()
    
    # Mocking behaviors
    async def evaluate_side_effect(script, *args):
        # 1. read_page call
        if "window.__generateAccessibilityTree" in script:
            return """
            role "button" "Target Button" [ref=ref_1]
            role "generic" "Overlay" [ref=ref_2]
            """
        
        # 2. Element lookup call
        # BrowserManager passes arguments to the script function wrapper
        # We can't easily check the script content for "browser_element_script.js" 
        # because it's loaded from file.
        # But we can assume subsequent calls are for element info.
        
        # We return a dict.
        # If the manager is checking safety or clicking, it calls element script.
        
        # Let's return isOccluded=True
        return {
            "success": True, 
            "coordinates": [10, 10], 
            "isOccluded": True, 
            "occludedBy": "Overlay",
            "attributes": {"text": "Target Button"}
        }

    manager.page.evaluate = AsyncMock(side_effect=evaluate_side_effect)

    try:
        # Load local test file
        file_path = os.path.abspath("tests/test_occlusion.html")
        url = f"file://{file_path}"
        await manager.execute_action("navigate", text=url)
        
        # Get accessibility tree to find the ref
        tree = await manager.execute_action("read_page")
        
        target_ref = "ref_1"
        assert target_ref in tree

        # Test 1: Normal click should fail due to occlusion
        result = await manager.execute_action("left_click", ref=target_ref)
        
        assert "Action Failed" in result
        assert "occluded by 'Overlay'" in result

        # Test 2: Force click should bypass the check (but physically still hit the overlay)
        # We just want to ensure the *Python* error is not raised and click is called
        result_force = await manager.execute_action("left_click", ref=target_ref, force=True)
        
        assert "Clicked element ref_1" in result_force
        assert "Action Failed" not in result_force
        
        # Verify click was called
        manager.page.mouse.click.assert_called()

    finally:
        await manager.close()