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
            
            await self.browser.navigate("https://www.google.com")
            
            # Первый скриншот для инициации
            capture_result = await self.browser.capture_annotated_screenshot()
            if capture_result is None:
                print("DEBUG: capture_annotated_screenshot returned None!")
                screenshot, elements = b"", []
            else:
                screenshot, elements = capture_result
            
            elements_text = self._format_elements_data(elements)
            
            self.history.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"Задача: {user_prompt}\n\nИнтерактивные элементы на странице:\n{elements_text}"),
                        types.Part.from_bytes(data=screenshot, mime_type="image/jpeg")
                    ]
                )
            )
            
            while True:
                console.print("[blue]Агент думает...[/blue]")
                
                try:
                    response = await self.agent.think(self.history)
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        console.print("[yellow]Предупреждение: Лимит запросов API (429). Ждем 10 секунд перед повтором...[/yellow]")
                        await asyncio.sleep(10)
                        continue
                    else:
                        raise e
                
                if not response.candidates:
                    if not hasattr(self, 'recovery_attempts'):
                        self.recovery_attempts = 0
                    
                    self.recovery_attempts += 1
                    console.print(f"[yellow]Предупреждение: Модель не дала ответа (попытка восстановления {self.recovery_attempts}/2).[/yellow]")
                    
                    if self.recovery_attempts <= 2:
                        # Откатываем историю (удаляем последнее сообщение пользователя, которое привело к сбою)
                        if self.history and self.history[-1].role == "user":
                            self.history.pop()
                        
                        # Добавляем сообщение об ошибке для модели
                        self.history.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_text(text="Предыдущий запрос вызвал ошибку API (пустой ответ). Пожалуйста, попробуй другое действие или упрости свой следующий шаг.")
                                ]
                            )
                        )
                        continue
                    else:
                        console.print("[red]Критическая ошибка: Модель не дает ответа после нескольких попыток.[/red]")
                        if hasattr(response, 'prompt_feedback'):
                             console.print(f"Feedback: {response.prompt_feedback}")
                        break
                
                # Сбрасываем счетчик при успешном ответе
                self.recovery_attempts = 0
                
                candidate = response.candidates[0]
                self.history.append(candidate.content) # Роль 'model'
                
                # Проверяем вызовы инструментов
                if candidate.content.parts:
                    tool_calls = [part.function_call for part in candidate.content.parts if part.function_call]
                else:
                    tool_calls = []
                
                if not tool_calls:
                    if candidate.content.parts:
                        text_parts = [p.text for p in candidate.content.parts if p.text]
                        if text_parts:
                            console.print(f"[yellow]Агент:[/yellow] {text_parts[0]}")
                            # Добавляем пинок, если агент просто болтает
                            self.history.append(
                                types.Content(
                                    role="user",
                                    parts=[types.Part.from_text(text="Продолжай выполнение задачи. Используй инструменты.")]
                                )
                            )
                            continue
                        else:
                            console.print("[yellow]Агент не предложил действий и не дал текстового ответа.[/yellow]")
                    else:
                        console.print("[yellow]Агент вернул пустой ответ (без частей).[/yellow]")
                    
                    # Если мы здесь, значит модель тупит. Пробуем пинок.
                    if self.recovery_attempts < 2:
                        self.recovery_attempts += 1
                        console.print(f"[yellow]Попытка стимуляции агента ({self.recovery_attempts}/2)...[/yellow]")
                        self.history.append(
                            types.Content(
                                role="user",
                                parts=[types.Part.from_text(text="Ты не выбрал действие. Пожалуйста, проанализируй скриншот и используй инструмент для продвижения к цели.")]
                            )
                        )
                        continue
                    else:
                        console.print("[red]Агент застрял.[/red]")
                        break

                # Выполняем инструменты и собираем ответы
                responses_parts = []
                for call in tool_calls:
                    console.print(f"[green]Действие:[/green] {call.name}({call.args})")
                    
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
                        user_help = console.input("[bold yellow]Агенту нужна помощь. Что делать? (или 'exit' для выхода): [/bold yellow]")
                        if user_help.lower() == 'exit':
                            return
                        result = f"Пользователь подсказал: {user_help}"

                    responses_parts.append(
                        types.Part.from_function_response(
                            name=call.name,
                            response={"result": result}
                        )
                    )
                    
                    if call.name == "task_completed":
                        console.print(f"[bold green]Задача завершена![/bold green] {call.args.get('result', '')}")
                        return

                # После выполнения инструментов делаем новый скриншот и добавляем в историю как ответ пользователя
                capture_result = await self.browser.capture_annotated_screenshot()
                if capture_result is None:
                    print("DEBUG: capture_annotated_screenshot returned None inside loop!")
                    screenshot, elements = b"", []
                else:
                    screenshot, elements = capture_result
                
                elements_text = self._format_elements_data(elements)
                
                responses_parts.append(
                    types.Part.from_text(text=f"Текущее состояние страницы. Интерактивные элементы:\n{elements_text}")
                )
                responses_parts.append(
                    types.Part.from_bytes(data=screenshot, mime_type="image/jpeg")
                )
                
                self.history.append(
                    types.Content(
                        role="user",
                        parts=responses_parts
                    )
                )
                
                await asyncio.sleep(1)

        except Exception as e:
            import traceback
            traceback.print_exc()
            console.print(f"[bold red]Произошла ошибка в основном цикле:[/bold red] {str(e)}")
        finally:
            await self.browser.close()

    def _format_elements_data(self, elements: list[dict]) -> str:
        if not elements:
            return "Нет видимых интерактивных элементов."
            
        lines = []
        for el in elements:
            info = f"ID {el['id']}: <{el['tagName']}>"
            if el['text']:
                info += f" '{el['text']}'"
            if el['ariaLabel']:
                info += f" aria-label='{el['ariaLabel']}'"
            if el['placeholder']:
                info += f" placeholder='{el['placeholder']}'"
            if el['role']:
                info += f" role='{el['role']}'"
            lines.append(info)
        
        # Ограничиваем количество элементов в текстовом описании для экономии контекста
        if len(lines) > 50:
             lines = lines[:50] + ["...[Список элементов обрезан]..."]
             
        return "\n".join(lines) if lines else "Нет видимых интерактивных элементов."

    async def execute_tool(self, call):
        name = call.name
        args = call.args
        
        try:
            if name == "navigate":
                await self.browser.navigate(args["url"])
                return f"Перешли на {args['url']}"
            elif name == "update_plan":
                self.agent.update_plan(args["steps"], args["current_step_index"])
                return "План обновлен"
            elif name == "save_memory":
                self.agent.save_memory(args["key"], args["value"])
                return f"Сохранено в память: {args['key']} = {args['value']}"
            elif name == "go_back":
                await self.browser.go_back()
                return "Вернулись назад"
            elif name == "go_forward":
                await self.browser.go_forward()
                return "Перешли вперед"
            elif name == "reload":
                await self.browser.reload()
                return "Страница перезагружена"
            elif name == "click_element":
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
            elif name == "extract_content":
                content = await self.browser.extract_content()
                # Ограничим длину для истории, чтобы не перегружать контекст (но отправим всё в историю)
                return content
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
