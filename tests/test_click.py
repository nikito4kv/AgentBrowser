import pytest
import os
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_click_element():
    manager = BrowserManager()
    await manager.start()
    
    file_path = "file://" + os.path.abspath("tests/test_page.html")
    await manager.navigate(file_path)
    
    # Сначала нужно разметить страницу, чтобы появились data-agent-id
    await manager.capture_annotated_screenshot()
    
    # Кликаем по кнопке (id=btn1, должна получить data-agent-id=1)
    success = await manager.click_element(1)
    assert success is True
    
    # Проверяем результат
    button_text = await manager.page.inner_text("#btn1")
    assert button_text == "Clicked"
    
    await manager.close()
