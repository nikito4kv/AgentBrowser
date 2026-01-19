import os
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright

class BrowserManager:
    def __init__(self, user_data_dir: str = "user_data_dir", headless: bool = False):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.browser = None 

    async def start(self):
        self.playwright = await async_playwright().start()
        absolute_user_data_dir = os.path.abspath(self.user_data_dir)
        
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=absolute_user_data_dir,
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"], # Basic stealth
            viewport={"width": 1280, "height": 720}
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        # For test compatibility, treating context as the browser instance roughly
        self.browser = self.context

    async def navigate(self, url: str):
        if self.page:
            await self.page.goto(url)

    async def capture_annotated_screenshot(self) -> bytes:
        if not self.page:
            raise RuntimeError("Page not initialized. Call start() first.")
            
        # Инжектируем скрипт разметки
        js_path = os.path.join(os.path.dirname(__file__), "annotate.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()
            
        await self.page.evaluate(js_code)
        
        # Делаем скриншот
        return await self.page.screenshot(type="png", full_page=False)

    async def click_element(self, label_id: int) -> bool:
        if not self.page:
            return False
        
        selector = f"[data-agent-id='{label_id}']"
        element = await self.page.query_selector(selector)
        if element:
            await element.click()
            return True
        return False

    async def close(self):
        if self.context:
            await self.context.close()
            self.context = None
            self.page = None
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
