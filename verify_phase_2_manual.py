import asyncio
from agentbrowser.browser.manager import BrowserManager

async def main():
    print("Launching BrowserManager...")
    mgr = BrowserManager(headless=True)
    await mgr.start()
    
    print("Navigating to example.com...")
    await mgr.navigate('https://www.example.com')
    
    print("Capturing annotated screenshot and metadata...")
    screenshot_bytes, elements_data = await mgr.capture_annotated_screenshot()
    
    print(f"Got {len(elements_data)} elements.")
    
    if len(elements_data) > 0:
        el = elements_data[0]
        print(f"First element metadata: {el}")
        
        required_keys = ['tagName', 'text', 'ariaLabel', 'placeholder', 'title', 'role']
        missing = [k for k in required_keys if k not in el]
        
        if missing:
            print(f"FAILED: Missing keys in metadata: {missing}")
        else:
            print("SUCCESS: All required metadata keys are present.")
    else:
        print("WARNING: No elements found on example.com. Try a different site if needed.")

    await mgr.close()

if __name__ == "__main__":
    asyncio.run(main())
