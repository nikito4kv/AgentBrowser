import pytest
from agentbrowser.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_extract_content_limit():
    manager = BrowserManager()
    await manager.start()
    
    # Создаем длинный HTML
    long_text = "This is a long text. " * 1000
    html_content = f"<html><body><p>{long_text}</p></body></html>"
    await manager.page.set_content(html_content)
    
    md_text = await manager.extract_content()
    
    # Проверяем, что текст обрезан (лимит 10000)
    assert len(md_text) <= 10100 # небольшой запас на разметку и сообщение об обрезке
    assert "...[Контент обрезан для экономии контекста]..." in md_text
    
    await manager.close()
