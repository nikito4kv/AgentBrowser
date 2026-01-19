import asyncio
import os
from agentbrowser.browser.manager import BrowserManager

async def main():
    print("Запуск BrowserManager...")
    mgr = BrowserManager(headless=False)
    await mgr.start()
    
    print("Переход на google.com...")
    await mgr.navigate('https://www.google.com')
    
    print("Захват размеченного скриншота...")
    screenshot_bytes = await mgr.capture_annotated_screenshot()
    
    output_path = "google_annotated.png"
    with open(output_path, "wb") as f:
        f.write(screenshot_bytes)
    
    print(f"Скриншот сохранен: {os.path.abspath(output_path)}")
    print("Проверьте наличие красных меток на скриншоте.")
    
    print("Закрытие браузера через 5 секунд...")
    await asyncio.sleep(5)
    await mgr.close()

if __name__ == "__main__":
    asyncio.run(main())
