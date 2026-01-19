import pytest
import os
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_scroll_and_wait():
    manager = BrowserManager()
    await manager.start()
    
    # Создадим длинную страницу для теста скролла
    html_content = """
    <html>
    <body style="height: 2000px;">
        <div id="top">Top</div>
        <div id="bottom" style="position: absolute; top: 1500px;">Bottom</div>
    </body>
    </html>
    """
    await manager.page.set_content(html_content)
    
    # Скроллим вниз
    await manager.scroll("down")
    # Проверяем позицию скролла
    scroll_y = await manager.page.evaluate("window.scrollY")
    assert scroll_y > 0
    
    # Скроллим вверх
    await manager.scroll("up")
    scroll_y = await manager.page.evaluate("window.scrollY")
    assert scroll_y < 100 # Ожидаем возврат к верху
    
    await manager.close()
