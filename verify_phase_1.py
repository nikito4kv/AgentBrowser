import asyncio
import os
from agentbrowser.browser.manager import BrowserManager

async def main():
    print("Starting BrowserManager...")
    mgr = BrowserManager(headless=False)
    await mgr.start()
    print("Browser started.")
    
    print("Navigating to https://example.com...")
    await mgr.navigate('https://example.com')
    
    title = await mgr.page.title()
    print(f"Page Title: {title}")
    
    print("Closing browser in 2 seconds...")
    await asyncio.sleep(2)
    await mgr.close()
    print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
