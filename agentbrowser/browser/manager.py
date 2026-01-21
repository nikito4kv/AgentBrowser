import os
import asyncio
import json
import base64
from pathlib import Path
from typing import Any, Literal, Optional, Dict
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from playwright_stealth import Stealth
from google import genai
from google.genai import types

# Directory containing browser tool utility files (JS scripts)
BROWSER_TOOL_UTILS_DIR = Path(__file__).parent / "utils"

class SecurityRiskError(Exception):
    """Exception raised when an action is deemed risky and requires confirmation."""
    def __init__(self, message, risk_details):
        super().__init__(message)
        self.risk_details = risk_details

class BrowserManager:
    RISKY_KEYWORDS = ["delete", "удалить", "buy", "купить", "pay", "оплатить", "send", "отправить", "confirm", "подтвердить", "order", "заказ", "checkout", "оформить"]

    def __init__(self, user_data_dir: str = "user_data_dir", headless: bool = False, api_key: str = None):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.browser = None
        
        self.width = 1280
        self.height = 800
        
        # Initialize Gemini client for the 'find' tool
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            print("Warning: No API Key provided. The 'find' tool will not use AI.")
            self.client = None

    async def start(self):
        self.playwright = await async_playwright().start()
        absolute_user_data_dir = os.path.abspath(self.user_data_dir)
        
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=absolute_user_data_dir,
            headless=self.headless,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--disable-infobars"
            ],
            viewport={"width": self.width, "height": self.height}
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
            
        await Stealth().apply_stealth_async(self.page)
        self.browser = self.context

    async def _execute_js_from_file(self, filename: str, *args) -> Any:
        """Load and execute JavaScript from a file."""
        if not self.page:
            return None

        script_path = BROWSER_TOOL_UTILS_DIR / filename
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {filename}")

        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read()

        # Special handling for browser_dom_script.js
        if filename == "browser_dom_script.js":
            filter_type = args[0] if args else ""
            # Wrap in IIFE to return the result of window.__generateAccessibilityTree
            combined_expression = f"""
                (function() {{
                    {script}
                    return window.__generateAccessibilityTree('{filter_type}');
                }})()
            """
            return await self.page.evaluate(combined_expression)
        else:
            # For other scripts, wrap as a function and call with arguments
            escaped_args = ", ".join(json.dumps(arg) for arg in args)
            js_expression = f"({script})({escaped_args})"
            return await self.page.evaluate(js_expression)

    async def capture_screenshot(self) -> bytes:
        if not self.page:
            return b""
        try:
            # Stabilization: Attempt to wait for network to be idle, but don't hang forever
            try:
                await self.page.wait_for_load_state("networkidle", timeout=1000)
            except:
                pass # Continue if it times out (some pages never idle)
                
            return await self.page.screenshot(type="jpeg", quality=80, full_page=False)
        except Exception as e:
            print(f"Screenshot error: {e}")
            return b""

    async def _navigate(self, url: str) -> str:
        if not self.page: return "Browser not started"
        try:
            if not url.startswith(("http://", "https://", "file://", "about:")):
                url = f"https://{url}"
            await self.page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(2) # Stabilize
            return f"Navigated to {url}"
        except Exception as e:
            return f"Navigation failed: {e}"

# ... (inside _type_text) ...

    async def _check_click_safety(self, ref: str = None, force: bool = False):
        """Checks if a click action is potentially destructive."""
        if force: return True
        if not ref: return True # Cannot check non-ref clicks easily, assuming coordinate clicks are intentional or fallback

        try:
            element_info = await self._execute_js_from_file("browser_element_script.js", ref)
            if not element_info or not element_info.get("success", False):
                return True # Element not found, let the click logic handle the error
            
            attributes = element_info.get("attributes", {})
            text = attributes.get("text", "").lower()
            aria_label = attributes.get("ariaLabel", "").lower()
            
            # Combine text sources
            full_text = f"{text} {aria_label}"
            
            for keyword in self.RISKY_KEYWORDS:
                if keyword in full_text:
                    raise SecurityRiskError(
                        f"Potentially destructive action detected: Click on element containing '{keyword}'",
                        risk_details=f"Element Text: '{attributes.get('text')}' | Aria-Label: '{attributes.get('ariaLabel')}'"
                    )
                    
        except SecurityRiskError:
            raise
        except Exception as e:
            print(f"Safety check warning: {e}")
            # Fail open or closed? Let's fail open but log it for now to avoid blocking harmless actions on error
            pass

    async def _click(self, action: str, coordinate: list[int] = None, ref: str = None, force: bool = False) -> str:
        if not self.page: return "Browser not started"
        
        try:
            # Security Check
            if ref:
                await self._check_click_safety(ref, force)

            button = "left"
            if action == "right_click": button = "right"
            elif action == "middle_click": button = "middle"
            
            click_count = 1
            if action == "double_click": click_count = 2
            
            if coordinate:
                x, y = coordinate
                # Simple validation
                if x < 0 or x > self.width or y < 0 or y > self.height:
                    print(f"Warning: Click coordinates {x},{y} out of bounds")
                
                await self.page.mouse.click(x, y, button=button, click_count=click_count)
                return f"Clicked at {x}, {y}"
                
            elif ref:
                element_info = await self._execute_js_from_file("browser_element_script.js", ref)
                if not element_info.get("success", False):
                    return f"Failed to find element ref: {ref}"
                
                # Occlusion Check
                if element_info.get("isOccluded", False) and not force:
                    occluded_by = element_info.get("occludedBy", "unknown element")
                    return f"Action Failed: Element {ref} is occluded by '{occluded_by}'. Use force=True to click anyway, or close the obstructing element."

                x, y = element_info["coordinates"]
                await self.page.mouse.click(x, y, button=button, click_count=click_count)
                return f"Clicked element {ref} at {x}, {y}"
                
            return "Error: No coordinate or ref provided for click"
        except SecurityRiskError:
            raise
        except Exception as e:
            return f"Click failed: {e}"

    async def _type_text(self, text: str, ref: str = None, force: bool = False) -> str:
        if not self.page: return "Browser not started"
        try:
            if ref:
                # Reliability Upgrade:
                # 1. Get exact coordinates
                element_info = await self._execute_js_from_file("browser_element_script.js", ref)
                
                if element_info and element_info.get("success"):
                     x, y = element_info["coordinates"]
                     
                     # 2. Hard Click to focus (Triple click selects all text if present, ensuring focus)
                     await self.page.mouse.click(x, y, click_count=3)
                     await asyncio.sleep(0.1)
                     
                     # 3. Press Backspace to clear selected text (if any)
                     await self.page.keyboard.press("Backspace")
            
            # 4. Type cleanly
            await self.page.keyboard.type(text, delay=50)
            return f"Typed: {text}"
        except SecurityRiskError:
            raise
        except Exception as e:
            return f"Type failed: {e}"

    async def _scroll(self, direction: str, amount: int = None, ref: str = None) -> str:
        if not self.page: return "Browser not started"
        try:
            if ref:
                 element_info = await self._execute_js_from_file("browser_element_script.js", ref)
                 if not element_info.get("success", False):
                    return f"Failed to find element to scroll: {ref}"
                 # The script handles scrollIntoView but we might want more specific scrolling
                 # For now, let's just say we scrolled to it
                 return f"Scrolled to element {ref}"
            
            # Global scroll
            if not amount: amount = 300 # Default pixels
            delta_x, delta_y = 0, 0
            
            if direction == "down": delta_y = amount
            elif direction == "up": delta_y = -amount
            elif direction == "left": delta_x = -amount
            elif direction == "right": delta_x = amount
            
            await self.page.mouse.wheel(delta_x, delta_y)
            await asyncio.sleep(0.5)
            return f"Scrolled {direction} by {amount}"
        except Exception as e:
            return f"Scroll failed: {e}"

    async def _read_page(self) -> str:
        if not self.page: return "Browser not started"
        try:
            dom_tree = await self._execute_js_from_file("browser_dom_script.js", "interactive")
            if isinstance(dom_tree, dict) and "pageContent" in dom_tree:
                return dom_tree["pageContent"]
            return str(dom_tree)
        except Exception as e:
            return f"Read page failed: {e}"

    async def _find(self, search_query: str) -> str:
        if not self.page: return "Browser not started"
        if not self.client: return "AI Search unavailable (No API Key)"
        
        try:
            # 1. Get the DOM Tree (All elements)
            dom_tree = await self._execute_js_from_file("browser_dom_script.js", "all")
            dom_content = dom_tree["pageContent"] if isinstance(dom_tree, dict) else str(dom_tree)
            
            # 2. Ask Gemini to find the element
            prompt = f"""
            You are helping find elements on a web page. The user wants to find: "{search_query}"

            Here is the accessibility tree of the page:
            {dom_content}

            Find ALL elements that match the user's query. Return up to 20 most relevant matches.
            
            Return your findings in this exact format (one line per matching element):

            FOUND: <total_number>
            ---
            ref_X | role | name | type | reason why this matches
            ...
            
            If no matches, return:
            FOUND: 0
            ERROR: explanation
            """
            
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            return response.text
        except Exception as e:
            return f"Find failed: {e}"

    async def execute_action(self, action: str, force: bool = False, **kwargs) -> str:
        """Universal entry point for tool actions"""
        await self.start() if not self.browser else None
        
        print(f"Executing action: {action} with args: {kwargs} (force={force})")
        
        if action == "navigate":
            return await self._navigate(kwargs.get("text", ""))
        elif action in ["left_click", "right_click", "double_click", "middle_click"]:
            return await self._click(action, coordinate=kwargs.get("coordinate"), ref=kwargs.get("ref"), force=force)
        elif action == "type":
            return await self._type_text(kwargs.get("text", ""), ref=kwargs.get("ref"), force=force)
        elif action == "scroll":
             return await self._scroll(
                 kwargs.get("scroll_direction", "down"), 
                 kwargs.get("scroll_amount", 300), 
                 kwargs.get("ref")
             )
        elif action == "read_page":
            return await self._read_page()
        elif action == "find":
            return await self._find(kwargs.get("text", ""))
        elif action == "wait":
            await asyncio.sleep(kwargs.get("duration", 1))
            return f"Waited {kwargs.get('duration')}s"
        elif action == "key":
            key = kwargs.get("text")
            await self.page.keyboard.press(key)
            return f"Pressed key {key}"
        elif action == "screenshot":
            return "Screenshot taken (visual state refreshed)"
            
        return f"Unknown action: {action}"

    async def close(self):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()