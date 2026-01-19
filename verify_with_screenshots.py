import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from agentbrowser.browser.manager import BrowserManager
from agentbrowser.agent.logic import Agent
from rich.console import Console
from google.genai import types

load_dotenv()
console = Console()

class DebugOrchestrator:
    def __init__(self, api_key: str, debug_dir: str):
        self.browser = BrowserManager(headless=False)
        self.agent = Agent(api_key=api_key)
        self.history = []
        self.debug_dir = debug_dir
        self.step_count = 0
        self.recovery_attempts = 0
        os.makedirs(debug_dir, exist_ok=True)
        self.log_file = open(os.path.join(debug_dir, "log.txt"), "w", encoding="utf-8")

    def log(self, message):
        console.print(message)
        self.log_file.write(message + "\n")
        self.log_file.flush()

    async def save_debug_screenshot(self, suffix=""):
        # Используем существующий метод, но сохраняем результат
        screenshot, _ = await self.browser.capture_annotated_screenshot()
        if screenshot:
            filename = f"step_{self.step_count:03d}{suffix}.jpg"
            path = os.path.join(self.debug_dir, filename)
            with open(path, "wb") as f:
                f.write(screenshot)
            self.log(f"[DEBUG] Screenshot saved: {path}")
        return screenshot

    async def run(self, user_prompt: str):
        await self.browser.start()
        try:
            self.log(f"[bold blue]Задача:[/bold blue] {user_prompt}")
            
            await self.browser.navigate("https://www.google.com")
            
            # Init screenshot
            screenshot, elements = await self.browser.capture_annotated_screenshot()
            await self.save_debug_screenshot("_init")
            
            elements_text = self._format_elements_data(elements)
            
            self.history.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"Задача: {user_prompt}\n\nИнтерактивные элементы:\n{elements_text}"),
                        types.Part.from_bytes(data=screenshot, mime_type="image/jpeg")
                    ]
                )
            )
            
            while True:
                self.step_count += 1
                self.log(f"\n--- STEP {self.step_count} ---")
                self.log("[blue]Агент думает...[/blue]")
                
                try:
                    response = await self.agent.think(self.history)
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        self.log("[yellow]API Limit (429). Waiting 10s...[/yellow]")
                        await asyncio.sleep(10)
                        continue
                    else:
                        raise e
                
                if not response.candidates:
                    self.log("[yellow]No candidates returned.[/yellow]")
                    if self.recovery_attempts < 2:
                        self.recovery_attempts += 1
                        if self.history and self.history[-1].role == "user":
                            self.history.pop()
                        self.history.append(types.Content(role="user", parts=[types.Part.from_text("Error: Empty response. Try again.")]))
                        continue
                    else:
                        break

                candidate = response.candidates[0]
                if not candidate.content:
                    self.log("[yellow]Candidate content is None.[/yellow]")
                    continue

                self.history.append(candidate.content)
                
                tool_calls = []
                if candidate.content.parts:
                    tool_calls = [p.function_call for p in candidate.content.parts if p.function_call]
                
                if not tool_calls:
                    if candidate.content.parts:
                        text_parts = [p.text for p in candidate.content.parts if p.text]
                        if text_parts:
                            self.log(f"[yellow]Агент:[/yellow] {text_parts[0]}")
                            # Kick
                            self.history.append(types.Content(role="user", parts=[types.Part.from_text("Продолжай. Используй инструменты.")]))
                            continue
                    
                    self.log("[yellow]Агент молчит.[/yellow]")
                    break

                # Execute tools
                responses_parts = []
                for call in tool_calls:
                    self.log(f"[green]Действие:[/green] {call.name}({call.args})")
                    
                    result = await self.execute_tool(call)
                    self.log(f"Result: {result}")
                    
                    responses_parts.append(
                        types.Part.from_function_response(
                            name=call.name,
                            response={"result": result}
                        )
                    )
                    
                    if call.name == "task_completed":
                        self.log(f"[bold green]COMPLETE:[/bold green] {call.args.get('result')}")
                        return

                # New screenshot
                screenshot, elements = await self.browser.capture_annotated_screenshot()
                await self.save_debug_screenshot()
                elements_text = self._format_elements_data(elements)
                
                responses_parts.append(types.Part.from_text(text=f"Состояние страницы. Элементы:\n{elements_text}"))
                responses_parts.append(types.Part.from_bytes(data=screenshot, mime_type="image/jpeg"))
                
                self.history.append(types.Content(role="user", parts=responses_parts))
                await asyncio.sleep(1)

        except Exception as e:
            import traceback
            traceback.print_exc(file=self.log_file)
            self.log(f"[bold red]ERROR:[/bold red] {str(e)}")
        finally:
            self.log_file.close()
            await self.browser.close()

    # Reuse methods from main.py (copy-paste logic for brevity in this standalone script)
    def _format_elements_data(self, elements: list[dict]) -> str:
        if not elements: return "Нет элементов."
        lines = [f"ID {el['id']}: <{el['tagName']}> '{el['text']}'" for el in elements[:50]]
        return "\n".join(lines)

    async def execute_tool(self, call):
        # Simplified execution for debug
        name = call.name
        args = call.args
        if name == "navigate": await self.browser.navigate(args["url"]); return f"Navigated to {args['url']}"
        if name == "update_plan": self.agent.update_plan(args["steps"], args["current_step_index"]); return "Plan updated"
        if name == "click_element": return "Success" if await self.browser.click_element(args["label_id"]) else "Failed"
        if name == "type_text": return "Success" if await self.browser.type_text(args["label_id"], args["text"]) else "Failed"
        if name == "scroll": await self.browser.scroll(args["direction"]); return "Scrolled"
        if name == "wait": await self.browser.wait(args["seconds"]); return "Waited"
        if name == "extract_content": return await self.browser.extract_content()
        if name == "task_completed": return "Done"
        return "Unknown tool"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_with_screenshots.py <prompt>")
        sys.exit(1)
        
    api_key = os.getenv("GEMINI_API_KEY")
    ts = int(time.time())
    debug_dir = f"debug_screenshots/run_{ts}"
    print(f"Debug artifacts will be saved to: {debug_dir}")
    
    orch = DebugOrchestrator(api_key, debug_dir)
    asyncio.run(orch.run(sys.argv[1]))
