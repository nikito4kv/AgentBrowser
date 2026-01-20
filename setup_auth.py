import asyncio
import os
from playwright.async_api import async_playwright

async def setup_auth():
    """
    Запускает браузер с постоянным профилем для ручной авторизации.
    """
    user_data_dir = "user_data_dir"
    absolute_user_data_dir = os.path.abspath(user_data_dir)
    
    print(f"--- РЕЖИМ РУЧНОЙ АВТОРИЗАЦИИ ---")
    print(f"Профиль браузера: {absolute_user_data_dir}")
    print("Браузер откроется через несколько секунд.")
    print("1. Зайдите на нужные сайты (Яндекс, HH.ru, Gmail и т.д.).")
    print("2. Выполните вход (Login).")
    print("3. Нажмите 'Запомнить меня'.")
    print("4. Когда закончите, закройте окно браузера или нажмите Ctrl+C здесь.")
    
    async with async_playwright() as p:
        # Запускаем браузер с постоянным контекстом (Persistent Context)
        # headless=False обязательно, чтобы пользователь мог видеть браузер
        context = await p.chromium.launch_persistent_context(
            user_data_dir=absolute_user_data_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 720}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto("https://www.google.com")
        
        print("\nБраузер запущен. Нажмите 'Resume' в инспекторе Playwright (если открылся) или просто пользуйтесь браузером.")
        print("Скрипт ждет закрытия браузера...")
        
        # Используем page.pause() для остановки выполнения и открытия Playwright Inspector
        # Пользователь может пользоваться браузером сколько угодно
        await page.pause() 
        
        # Если page.pause() отпущен или браузер закрыт
        try:
            await context.close()
        except:
            pass
        print("Сессия завершена.")

if __name__ == "__main__":
    try:
        asyncio.run(setup_auth())
    except KeyboardInterrupt:
        print("\nПринудительное завершение.")
