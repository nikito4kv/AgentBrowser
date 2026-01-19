import asyncio
import os
from agentbrowser.browser.manager import BrowserManager

async def main():
    mgr = BrowserManager(headless=False)
    await mgr.start()
    
    print("Navigating to https://example.com...")
    await mgr.navigate("https://example.com")
    
    print("Extracting content...")
    content = await mgr.extract_content()
    
    print("-" * 20)
    print(content)
    print("-" * 20)
    
    if "Example Domain" in content:
        print("SUCCESS: Content extracted correctly!")
    else:
        print("FAILURE: Content extraction failed.")
        
    await asyncio.sleep(2)
    await mgr.close()

if __name__ == "__main__":
    asyncio.run(main())
