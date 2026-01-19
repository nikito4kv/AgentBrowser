import asyncio
import os
from agentbrowser.browser.manager import BrowserManager

async def main():
    print("Запуск BrowserManager...")
    mgr = BrowserManager(headless=False)
    await mgr.start()
    
    print("Переход на google.com...")
    await mgr.navigate('https://www.google.com')
    
    # Нужно разметить, чтобы найти ID поля ввода
    print("Разметка страницы...")
    await mgr.capture_annotated_screenshot()
    
    # Поле поиска Google обычно имеет ID 1 или около того на чистой странице
    # В реальности ID может меняться. Мы попробуем ввести текст в элемент, 
    # который кажется полем ввода (обычно это textarea или input).
    
    # Для надежности в верификации мы просто попробуем найти первый input/textarea
    elements = await mgr.page.query_selector_all("[data-agent-id]")
    search_id = None
    for el in elements:
        tag = await el.evaluate("el => el.tagName")
        if tag in ["INPUT", "TEXTAREA"]:
            search_id = await el.get_attribute("data-agent-id")
            break
            
    if search_id:
        print(f"Ввод 'Gemini AI' в элемент #{search_id}...")
        await mgr.type_text(int(search_id), "Gemini AI")
        await mgr.page.keyboard.press("Enter")
        await asyncio.sleep(3)
        
        print("Прокрутка результатов вниз...")
        await mgr.scroll("down")
        await asyncio.sleep(2)
    else:
        print("Не удалось найти поле поиска.")
    
    print("Закрытие браузера...")
    await mgr.close()

if __name__ == "__main__":
    asyncio.run(main())
