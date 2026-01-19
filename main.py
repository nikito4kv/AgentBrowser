import asyncio
import os
import sys
from dotenv import load_dotenv
from agentbrowser.browser.manager import BrowserManager
from agentbrowser.agent.logic import Agent
from rich.console import Console
from google.genai import types

load_dotenv()

console = Console()

class Orchestrator:
    def __init__(self, api_key: str):
        self.browser = BrowserManager(headless=False)
        self.agent = Agent(api_key=api_key)
        self.history = []

    async def run(self, user_prompt: str):
        await self.browser.start()
        try:
            console.print(f"[bold blue]Задача:[/bold blue] {user_prompt}")
            
            # Начальная навигация на google, если мы еще нигде
            await self.browser.navigate("https://www.google.com")
            
            while True:
                console.print("[blue]Агент думает...[/blue]")
                
                # 1. Observe
                screenshot = await self.browser.capture_annotated_screenshot()
                
                # 2. Think
                response = await self.agent.think(user_prompt, screenshot, self.history)
                
                # Анализируем ответ
                if not response.candidates:
                    console.print("[red]Нет ответа от модели.[/red]")
                    break
                    
                candidate = response.candidates[0]
                self.history.append(candidate.content)
                
                # Проверяем вызовы инструментов
                tool_calls = [part.call for part in candidate.content.parts if part.call]
                
                if not tool_calls:
                    if candidate.content.parts:
                        text_parts = [p.text for p in candidate.content.parts if p.text]
                        if text_parts:
                            console.print(f"[yellow]Агент:[/yellow] {text_parts[0]}")
                    break

                for call in tool_calls:
                    console.print(f"[green]Действие:[/green] {call.name}({call.args})")
                    
                    # Retry механизм
                    max_retries = 3
                    result = "Ошибка"
                    for attempt in range(max_retries):
                        result = await self.execute_tool(call)
                        if "Ошибка" not in result and "Элемент не найден" not in result:
                            break
                        console.print(f"[yellow]Попытка {attempt+1} не удалась: {result}. Пробую снова...[/yellow]")
                        await asyncio.sleep(2)
                    
                    if "Ошибка" in result or "Элемент не найден" in result:
                        console.print(f"[bold red]Критическая ошибка:[/bold red] {result}")
                        # Здесь можно добавить input() для запроса помощи у пользователя
                        user_help = console.input("[bold yellow]Агенту нужна помощь. Что делать? (или 'exit' для выхода): [/bold yellow]")
                        if user_help.lower() == 'exit':
                            return
                        result = f"Пользователь подсказал: {user_help}"

                    # Передаем результат обратно в историю
                    self.history.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_function_response(
                                name=call.name,
                                response={"result": result}
                            )]
                        )
                    )
                    
                    if call.name == "task_completed":
                        console.print(f"[bold green]Задача завершена![/bold green] {call.args.get('result', '')}")
                        return
                
                # Небольшая пауза между шагами
                await asyncio.sleep(1)

        finally:
            await self.browser.close()

    async def execute_tool(self, call):
        name = call.name
        args = call.args
        
        try:
            if name == "click_element":
                success = await self.browser.click_element(args["label_id"])
                return "Успешно" if success else "Элемент не найден"
            elif name == "type_text":
                success = await self.browser.type_text(args["label_id"], args["text"])
                return "Успешно" if success else "Элемент не найден"
            elif name == "scroll":
                await self.browser.scroll(args["direction"])
                return "Прокручено"
            elif name == "wait":
                await self.browser.wait(args["seconds"])
                return "Подождали"
            elif name == "task_completed":
                return "Завершено"
            else:
                return f"Неизвестный инструмент: {name}"
        except Exception as e:
            return f"Ошибка при выполнении: {str(e)}"

async def main():
    if len(sys.argv) < 2:
        console.print("[red]Укажите задачу в кавычках.[/red]")
        return
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]GEMINI_API_KEY не найден в .env[/red]")
        return
        
    prompt = sys.argv[1]
    orchestrator = Orchestrator(api_key)
    await orchestrator.run(prompt)

if __name__ == "__main__":
    asyncio.run(main())