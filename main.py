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
        self.planner = Agent(api_key=api_key, role="planner")
        self.actor = Agent(api_key=api_key, role="actor")
        self.history = [] # Planner's history
        self.user_prompt = ""
        self.step_count = 0
        import time
        self.debug_dir = f"debug_screenshots/run_{int(time.time())}"
        os.makedirs(self.debug_dir, exist_ok=True)

    def save_debug_image(self, screenshot_bytes, suffix=""):
        if not screenshot_bytes: return
        filename = f"step_{self.step_count:03d}{suffix}.jpg"
        path = os.path.join(self.debug_dir, filename)
        with open(path, "wb") as f:
            f.write(screenshot_bytes)
        # console.print(f"[dim]Saved debug image: {path}[/dim]")

    async def run(self, user_prompt: str):
        self.user_prompt = user_prompt
        await self.browser.start()
        try:
            console.print(f"[bold blue]Задача:[/bold blue] {user_prompt}")
            
            # Navigate to initial page if needed or just start blank
            await self.browser.navigate("https://www.google.com")
            
            # Initial screenshot for Planner
            capture_result = await self.browser.capture_annotated_screenshot()
            if capture_result is None:
                screenshot, elements = b"", []
            else:
                screenshot, elements = capture_result
            
            self.save_debug_image(screenshot, "_init")
            elements_text = self._format_elements_data(elements)
            
            # Initial message to Planner
            self.history.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"GOAL: {user_prompt}\n\nCurrent State:\n{elements_text}"),
                        types.Part.from_bytes(data=screenshot, mime_type="image/jpeg")
                    ]
                )
            )
            
            while True:
                # Random delay for human-like behavior
                import random
                delay = random.uniform(1, 3)
                console.print(f"[dim gray]Waiting {delay:.1f}s...[/dim gray]")
                await asyncio.sleep(delay)
                
                console.print("[blue]Planner thinking...[/blue]")
                
                # PLANNER TURN
                try:
                    response = await self.planner.think(self.history)
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        wait_time = 15
                        console.print(f"[yellow]Planner API Limit (429). Waiting {wait_time}s...[/yellow]")
                        await asyncio.sleep(wait_time)
                        continue
                    console.print(f"[red]Planner API Error: {e}[/red]")
                    await asyncio.sleep(5)
                    continue

                if not response.candidates:
                    console.print("[red]Planner returned no candidates.[/red]")
                    continue
                    
                planner_content = response.candidates[0].content
                self.history.append(planner_content)
                
                # Print Planner's thoughts
                if planner_content.parts:
                    text_parts = [p.text for p in planner_content.parts if p.text]
                    if text_parts:
                        console.print(f"[bold cyan]Planner Thoughts:[/bold cyan]\n{text_parts[0]}")

                # Check for Tool Calls
                tool_calls = []
                if planner_content.parts:
                    tool_calls = [part.function_call for part in planner_content.parts if part.function_call]
                
                if not tool_calls:
                    # If Planner didn't call tools, prompt it
                    console.print("[yellow]Planner didn't call any tools. Reprompting...[/yellow]")
                    self.history.append(
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text="Please use a tool. If you want to act, use 'delegate_to_actor'. If finished, use 'task_completed'.")]
                        )
                    )
                    continue

                # Execute Planner Tools
                for call in tool_calls:
                    console.print(f"[magenta]Planner Tool:[/magenta] {call.name}")
                    
                    if call.name == "task_completed":
                        result = call.args.get('result', '')
                        console.print(f"[bold green]TASK COMPLETED:[/bold green] {result}")
                        return
                    
                    elif call.name == "task_failed":
                        reason = call.args.get('reason', '')
                        console.print(f"[bold red]TASK FAILED:[/bold red] {reason}")
                        return
                        
                    elif call.name == "delegate_to_actor":
                        instruction = call.args.get('instruction', '')
                        console.print(f"[bold yellow]Instruction for Actor:[/bold yellow] {instruction}")
                        
                        # ACTOR TURN
                        actor_result = await self.run_actor_turn(instruction)
                        
                        # Feed result back to Planner
                        # Capture new state after actor's action
                        self.step_count += 1
                        capture_result = await self.browser.capture_annotated_screenshot()
                        if capture_result is None:
                            new_screenshot, new_elements = b"", []
                        else:
                            new_screenshot, new_elements = capture_result
                        
                        self.save_debug_image(new_screenshot)
                        new_elements_text = self._format_elements_data(new_elements)
                        
                        self.history.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_function_response(
                                        name="delegate_to_actor",
                                        response={"result": actor_result}
                                    ),
                                    types.Part.from_text(text=f"Action executed. Current State:\n{new_elements_text}"),
                                    types.Part.from_bytes(data=new_screenshot, mime_type="image/jpeg")
                                ]
                            )
                        )
                    
                    else:
                        # Handle other planner tools (update_plan, save_memory, ask_user)
                        result = await self.execute_tool(call)
                        self.history.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_function_response(
                                        name=call.name,
                                        response={"result": str(result)}
                                    )
                                ]
                            )
                        )

        except Exception as e:
            import traceback
            traceback.print_exc()
            console.print(f"[bold red]Critical Error:[/bold red] {str(e)}")
        finally:
            await self.browser.close()

    async def run_actor_turn(self, instruction: str) -> str:
        console.print("[green]Actor working...[/green]")
        
        # Get fresh state for Actor
        capture_result = await self.browser.capture_annotated_screenshot()
        if capture_result is None:
            return "Error: Could not capture screenshot for Actor."
        screenshot, elements = capture_result
        elements_text = self._format_elements_data(elements)
        
        # Construct Actor prompt
        # We give it the specific instruction AND the global goal context
        actor_prompt = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=f"GLOBAL GOAL: {self.user_prompt}\n"
                        f"CURRENT INSTRUCTION: {instruction}\n\n"
                        f"Interactive Elements:\n{elements_text}"
                    ),
                    types.Part.from_bytes(data=screenshot, mime_type="image/jpeg")
                ]
            )
        ]
        
        try:
            response = await self.actor.think(actor_prompt)
        except Exception as e:
            return f"Actor API Error: {str(e)}"
            
        if not response.candidates:
            return "Actor returned no response."
            
        candidate = response.candidates[0]
        tool_calls = [part.function_call for part in candidate.content.parts if part.function_call]
        
        if not tool_calls:
            # Actor didn't pick a tool.
            if candidate.content.parts:
                text = candidate.content.parts[0].text
                return f"Actor didn't act, but said: {text}"
            return "Actor didn't act."
            
        # Execute Actor Tools
        # Actor usually performs one atomic action per instruction
        results = []
        for call in tool_calls:
            console.print(f"[green]Actor Action:[/green] {call.name}({call.args})")
            res = await self.execute_tool(call) # Reuse common execute_tool
            results.append(f"{call.name}: {res}")
            
        return "; ".join(results)

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
        
        if len(lines) > 50:
             lines = lines[:50] + ["...[Список элементов обрезан]..."]
             
        return "\n".join(lines) if lines else "Нет видимых интерактивных элементов."

    async def execute_tool(self, call):
        # This handles tools for both Planner (non-action) and Actor (action)
        # Note: navigate/reload are in both, but usually Actor does them.
        name = call.name
        args = call.args
        
        try:
            if name == "navigate":
                await self.browser.navigate(args["url"])
                return f"Перешли на {args['url']}"
            elif name == "update_plan":
                # Only Planner has this
                self.planner.update_plan(args["steps"], args["current_step_index"])
                return "План обновлен"
            elif name == "save_memory":
                # Planner has this
                self.planner.save_memory(args["key"], args["value"])
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
            elif name == "press_key":
                success = await self.browser.press_key(args["key"])
                return f"Нажата клавиша {args['key']}" if success else "Ошибка нажатия"
            elif name == "scroll":
                await self.browser.scroll(args["direction"])
                return "Прокручено"
            elif name == "wait":
                await self.browser.wait(args["seconds"])
                return "Подождали"
            elif name == "extract_content":
                content = await self.browser.extract_content()
                return content
            elif name == "ask_user":
                question = args["question"]
                console.print(f"[bold yellow]ВОПРОС АГЕНТА:[/bold yellow] {question}")
                answer = console.input("[bold green]Ваш ответ: [/bold green]")
                return f"Ответ пользователя: {answer}"
            elif name == "get_element_details":
                details = await self.browser.get_element_details(args["label_id"])
                return f"Детали элемента: {details}"
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