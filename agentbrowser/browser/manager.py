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
        png_bytes = await self.page.screenshot(type="png", full_page=False)
        
        # Оптимизация через Pillow
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(png_bytes))
        # Ресайз если слишком большой (например, макс 1024 по ширине)
        max_width = 1024
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        out_io = io.BytesIO()
        img.save(out_io, format="PNG", optimize=True)
        return out_io.getvalue()

    async def click_element(self, label_id: int) -> bool:
        if not self.page:
            return False
        
        selector = f"[data-agent-id='{label_id}']"
        element = await self.page.query_selector(selector)
        if element:
            try:
                # Попытка 1: Обычный клик с коротким таймаутом
                await element.click(timeout=2000)
                return True
            except Exception:
                # Если обычный клик не прошел (например, перекрытие), пробуем JS Click
                # Это надежнее, чем force=True, так как вызывает событие напрямую на элементе
                try:
                    await element.evaluate("el => el.click()")
                    return True
                except Exception:
                    # Если и JS не помог (маловероятно), пробуем Force Click как последнюю надежду
                    try:
                        await element.click(force=True, timeout=2000)
                        return True
                    except Exception:
                        pass
                        
        return False

    async def type_text(self, label_id: int, text: str) -> bool:
        if not self.page:
            return False
            
        selector = f"[data-agent-id='{label_id}']"
        element = await self.page.query_selector(selector)
        if element:
            try:
                # Попытка 1: Обычный ввод
                await element.fill("", timeout=2000)
                await element.type(text, timeout=2000)
                return True
            except Exception:
                # Попытка 2: JS ввод
                try:
                    js_code = """(el, val) => { 
                        el.value = val; 
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }"""
                    await element.evaluate(js_code, text)
                    return True
                except Exception:
                    pass
                    
        return False

    async def scroll(self, direction: str, amount: str = "window.innerHeight"):
        if not self.page:
            return
            
        if direction.lower() == "down":
            await self.page.evaluate(f"window.scrollBy(0, {amount})")
        elif direction.lower() == "up":
            await self.page.evaluate(f"window.scrollBy(0, -{amount})")

    async def wait(self, seconds: float):
        import asyncio
        await asyncio.sleep(seconds)

    async def close(self):
        if self.context:
            await self.context.close()
            self.context = None
            self.page = None
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
