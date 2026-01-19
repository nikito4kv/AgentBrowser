import pytest
import os
import io
from agentbrowser.browser.manager import BrowserManager
from PIL import Image

@pytest.mark.asyncio
async def test_annotated_screenshot():
    manager = BrowserManager()
    await manager.start()
    
    file_path = "file://" + os.path.abspath("tests/test_page.html")
    await manager.navigate(file_path)
    
    screenshot_bytes, elements = await manager.capture_annotated_screenshot()
    
    # Проверяем, что скриншот не пустой
    assert screenshot_bytes is not None
    assert len(screenshot_bytes) > 0
    assert len(elements) > 0
    
    # Можно попробовать открыть через PIL для базовой проверки формата
    img = Image.open(io.BytesIO(screenshot_bytes))
    assert img.format == "JPEG"
    
    await manager.close()