import asyncio
import os
from agentbrowser.browser.manager import BrowserManager

async def main():
    mgr = BrowserManager(headless=False)
    await mgr.start()
    
    file_path = "file://" + os.path.abspath("tests/test_overlap.html")
    await mgr.navigate(file_path)
    await mgr.capture_annotated_screenshot()
    
    print("Trying to click ID 1 (Target Button under Overlay)...")
    await mgr.click_element(1)
    
    text = await mgr.page.inner_text("#target-btn")
    print(f"Button Text: {text}")
    
    if text == "Clicked":
        print("SUCCESS: Clicked through overlay!")
    else:
        print("FAILURE: Click did not work.")
        
    await asyncio.sleep(2)
    await mgr.close()

if __name__ == "__main__":
    asyncio.run(main())
