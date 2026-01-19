import pytest
import os
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_type_text():
    manager = BrowserManager()
    await manager.start()
    
    file_path = "file://" + os.path.abspath("tests/test_page.html")
    await manager.navigate(file_path)
    
    # Сначала нужно разметить страницу
    await manager.capture_annotated_screenshot()
    
    # Вводим текст в поле (id=input1, должен получить data-agent-id=3)
    # Порядок элементов в annotate.js зависит от querySelectorAll
    # В test_page.html: button (1), a (2), input (3)
    
    test_text = "Hello Gemini"
    success = await manager.type_text(3, test_text)
    assert success is True
    
    # Проверяем результат
    input_value = await manager.page.input_value("#input1")
    assert input_value == test_text
    
    await manager.close()
