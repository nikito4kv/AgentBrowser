import pytest
import os
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_js_annotation():
    manager = BrowserManager()
    await manager.start()
    
    # Загружаем тестовую страницу
    file_path = "file://" + os.path.abspath("tests/test_page.html")
    await manager.navigate(file_path)
    
    # Путь к JS скрипту (пока не создан)
    js_path = "agentbrowser/browser/annotate.js"
    with open(js_path, "r", encoding="utf-8") as f:
        js_code = f.read()
    
    # Выполняем скрипт
    await manager.page.evaluate(js_code)
    
    # Проверяем, что элементы получили атрибуты data-agent-id
    # Ожидаем: button, a, input
    annotated_elements = await manager.page.query_selector_all("[data-agent-id]")
    assert len(annotated_elements) == 3
    
    # Проверяем наличие визуальных меток (лейблов)
    labels = await manager.page.query_selector_all(".agent-browser-label")
    assert len(labels) == 3
    
    await manager.close()
