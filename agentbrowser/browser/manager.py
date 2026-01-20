import os
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from playwright_stealth import stealth_async

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
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            viewport=None # Используем нативный размер окна
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        # Применяем stealth к странице
        await stealth_async(self.page)
            
        # For test compatibility, treating context as the browser instance roughly
        self.browser = self.context

    async def navigate(self, url: str):
        if self.page:
            await self.page.goto(url)

    async def capture_annotated_screenshot(self) -> tuple[bytes, list[dict]]:
        if not self.page:
            return b"", []
        
        # Инъекция JS для аннотации
        js_path = os.path.join(os.path.dirname(__file__), "annotate.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()
            
        try:
            # Ждем загрузки сети, чтобы не ловить destroyed context
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=2000)
            except:
                pass

            elements_data = await self.page.evaluate(js_code)
            if elements_data is None:
                elements_data = []
        except Exception as e:
            # Если контекст умер или JS упал, возвращаем пустой список
            print(f"Annotation error: {e}")
            elements_data = []
        
        # Делаем скриншот
        png_bytes = await self.page.screenshot(type="jpeg", quality=70, full_page=False)
        
        # Оптимизация через Pillow (дополнительный ресайз если нужно)
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
        # Конвертируем в RGB, так как JPEG не поддерживает альфа-канал (хотя скриншот уже jpeg, но pillow при открытии может дать RGB)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
            
        img.save(out_io, format="JPEG", quality=70, optimize=True)
        # print(f"DEBUG: Returning screenshot {len(out_io.getvalue())} bytes and {len(elements_data)} elements")
        return out_io.getvalue(), elements_data

    async def click_element(self, label_id: int) -> bool:
        if not self.page:
            return False
        
        # Запоминаем текущий список страниц, чтобы отловить открытие новой вкладки
        initial_pages = self.context.pages
        
        selector = f"[data-agent-id='{label_id}']"
        element = await self.page.query_selector(selector)
        if element:
            try:
                # Попытка 1: Обычный клик с коротким таймаутом
                await element.click(timeout=2000)
                
                # Проверяем, не открылась ли новая вкладка
                if len(self.context.pages) > len(initial_pages):
                    # Переключаемся на новую вкладку
                    self.page = self.context.pages[-1]
                    await self.page.bring_to_front()
                    try:
                        await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except:
                        pass
                else:
                    # Обычное ожидание загрузки в текущей вкладке
                    try:
                        await self.page.wait_for_load_state("load", timeout=3000)
                    except:
                        pass
                        
                return True
            except Exception:
                # Если обычный клик не прошел (например, перекрытие), пробуем JS Click
                # Это надежнее, чем force=True, так как вызывает событие напрямую на элементе
                try:
                    await element.evaluate("el => el.click()")
                    
                    # Проверяем новую вкладку и для JS клика
                    if len(self.context.pages) > len(initial_pages):
                        self.page = self.context.pages[-1]
                        await self.page.bring_to_front()
                        try:
                            await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                        except:
                            pass
                    else:
                        try:
                            await self.page.wait_for_load_state("load", timeout=3000)
                        except:
                            pass
                    return True
                except Exception:
                    # Если и JS не помог (маловероятно), пробуем Force Click как последнюю надежду
                    try:
                        await element.click(force=True, timeout=2000)
                        try:
                            await self.page.wait_for_load_state("load", timeout=3000)
                        except:
                            pass
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
                if "\n" in text:
                    try:
                        await self.page.wait_for_load_state("load", timeout=3000)
                    except:
                        pass
                return True
            except Exception:
                # Попытка 2: JS ввод
                try:
                    js_code = """(el, val) => { 
                        el.value = val; 
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        if (val.includes('\\n')) {
                            el.form.submit();
                        }
                    }"""
                    await element.evaluate(js_code, text)
                    if "\n" in text:
                        try:
                            await self.page.wait_for_load_state("load", timeout=3000)
                        except:
                            pass
                    return True
                except Exception:
                    pass
                    
        return False

    async def press_key(self, key: str) -> bool:
        if not self.page:
            return False
        try:
            await self.page.keyboard.press(key)
            try:
                await self.page.wait_for_load_state("load", timeout=3000)
            except:
                pass
            return True
        except Exception as e:
            print(f"Error pressing key {key}: {e}")
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

    async def go_back(self):
        if self.page:
            await self.page.go_back()

    async def go_forward(self):
        if self.page:
            await self.page.go_forward()

    async def reload(self):
        if self.page:
            await self.page.reload()

    async def extract_content(self) -> str:
        if not self.page:
            return ""
        
        html = await self.page.content()
        from markdownify import markdownify
        md = markdownify(html, heading_style="ATX")
        
        # Лимитируем контент для стабильности модели
        limit = 10000
        if len(md) > limit:
            md = md[:limit] + "\n\n...[Контент обрезан для экономии контекста]..."
            
        return md.strip()

    async def get_element_details(self, label_id: int) -> dict:
        if not self.page:
            return {}
            
        selector = f"[data-agent-id='{label_id}']"
        element = await self.page.query_selector(selector)
        if not element:
            return {"error": "Element not found"}
            
        try:
            details = await element.evaluate("""el => {
                return {
                    tagName: el.tagName.toLowerCase(),
                    href: el.href || el.getAttribute('href') || '',
                    title: el.title || el.getAttribute('title') || '',
                    alt: el.alt || el.getAttribute('alt') || '',
                    innerText: el.innerText ? el.innerText.substring(0, 200) : '',
                    value: el.value || '',
                    type: el.type || '',
                    ariaLabel: el.getAttribute('aria-label') || ''
                }
            }""")
            return details
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        if self.context:
            await self.context.close()
            self.context = None
            self.page = None
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
