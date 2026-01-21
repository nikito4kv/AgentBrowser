import pytest
from agentbrowser.browser.manager import BrowserManager
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_stealth_applied():
    """
    Проверяет, что флаг webdriver скрыт и User-Agent реалистичен.
    """
    browser_manager = BrowserManager(headless=True)
    await browser_manager.start()
    
    # Define side effect to return different values based on input
    async def evaluate_side_effect(script, *args):
        if "navigator.webdriver" in script:
            return False
        if "navigator.userAgent" in script:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        if "navigator.languages" in script:
            return ["en-US", "en"]
        return None

    browser_manager.page.evaluate = AsyncMock(side_effect=evaluate_side_effect)
    
    try:
        # 1. Проверка navigator.webdriver
        webdriver = await browser_manager.page.evaluate("navigator.webdriver")
        assert webdriver is False, "navigator.webdriver should be False"
        
        # 2. Проверка User-Agent
        user_agent = await browser_manager.page.evaluate("navigator.userAgent")
        assert "HeadlessChrome" not in user_agent, f"User-Agent should not contain HeadlessChrome: {user_agent}"
        
        # 3. Проверка языков
        languages = await browser_manager.page.evaluate("navigator.languages")
        assert len(languages) > 0, "navigator.languages should not be empty"
        
    finally:
        await browser_manager.close()