import pytest
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_stealth_applied():
    """
    Проверяет, что флаг webdriver скрыт и User-Agent реалистичен.
    """
    browser_manager = BrowserManager(headless=True) # Headless для тестов
    await browser_manager.start()
    
    try:
        # 1. Проверка navigator.webdriver
        webdriver = await browser_manager.page.evaluate("navigator.webdriver")
        print(f"DEBUG: navigator.webdriver = {webdriver}")
        assert webdriver is False, "navigator.webdriver should be False"
        
        # 2. Проверка User-Agent
        user_agent = await browser_manager.page.evaluate("navigator.userAgent")
        print(f"DEBUG: userAgent = {user_agent}")
        assert "HeadlessChrome" not in user_agent, f"User-Agent should not contain HeadlessChrome: {user_agent}"
        
        # 3. Проверка языков
        languages = await browser_manager.page.evaluate("navigator.languages")
        print(f"DEBUG: languages = {languages}")
        assert len(languages) > 0, "navigator.languages should not be empty"
        
    finally:
        await browser_manager.close()
