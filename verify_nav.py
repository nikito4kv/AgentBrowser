import asyncio
import os
from agentbrowser.browser.manager import BrowserManager

async def main():
    mgr = BrowserManager(headless=False)
    await mgr.start()
    
    print("Navigating to example.com...")
    await mgr.navigate("https://example.com")
    await asyncio.sleep(2)
    
    print("Navigating to google.com...")
    await mgr.navigate("https://google.com")
    await asyncio.sleep(2)
    
    print("Going back (should be example.com)...")
    await mgr.go_back()
    title = await mgr.page.title()
    print(f"Title: {title}")
    await asyncio.sleep(2)
    
    print("Going forward (should be google.com)...")
    await mgr.go_forward()
    title = await mgr.page.title()
    print(f"Title: {title}")
    await asyncio.sleep(2)
    
    print("Reloading...")
    await mgr.reload()
    await asyncio.sleep(2)
    
    await mgr.close()

if __name__ == "__main__":
    asyncio.run(main())
