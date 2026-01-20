import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from agentbrowser.browser.manager import BrowserManager, SecurityRiskError
from agentbrowser.agent.logic import Agent
from google.genai import types

# Rich imports for UI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich import box

load_dotenv()

console = Console()

class Orchestrator:
    def __init__(self, api_key: str):
        self.browser = BrowserManager(headless=False, api_key=api_key)
        self.agent = Agent(api_key=api_key)
        self.history = [] 
        self.step_count = 0
        self.debug_dir = f"debug_screenshots/run_{int(time.time())}"
        os.makedirs(self.debug_dir, exist_ok=True)

    def save_debug_image(self, screenshot_bytes, suffix=""):
        if not screenshot_bytes: return
        filename = f"step_{self.step_count:03d}{suffix}.jpg"
        path = os.path.join(self.debug_dir, filename)
        with open(path, "wb") as f:
            f.write(screenshot_bytes)

    def print_agent_thought(self, text: str):
        if not text.strip(): return
        panel = Panel(
            Markdown(text),
            title="[bold purple]🧠 Agent Thought[/bold purple]",
            border_style="purple",
            box=box.ROUNDED,
            expand=False
        )
        console.print(panel)

    def print_tool_call(self, name: str, args: dict):
        # Format args beautifully
        args_str = "\n".join([f"[bold cyan]{k}[/bold cyan]: {v}" for k, v in args.items()])
        panel = Panel(
            args_str,
            title=f"[bold yellow]🛠️ Tool Call: {name}[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED,
            expand=False
        )
        console.print(panel)

    def print_tool_result(self, name: str, result: str):
        # Truncate long results for display
        display_result = result
        if len(result) > 500:
            display_result = result[:500] + f"\n... [Truncated {len(result)-500} chars] ..."
            
        panel = Panel(
            Text(display_result, style="dim white"),
            title=f"[bold green]✅ Result: {name}[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            expand=False
        )
        console.print(panel)

    async def run_task(self, user_prompt: str):
        # Ensure browser is started
        if not self.browser.page:
            with console.status("[bold blue]Launching Browser...[/bold blue]"):
                await self.browser.start()
                if not self.browser.page.url or self.browser.page.url == "about:blank":
                    await self.browser.navigate("https://www.google.com")

        console.rule(f"[bold blue]🚀 NEW GOAL[/bold blue]")
        console.print(Panel(user_prompt, border_style="blue", box=box.DOUBLE))
        
        # Initial State
        with console.status("[bold cyan]Capturing initial state...[/bold cyan]"):
            screenshot = await self.browser.capture_screenshot()
            self.save_debug_image(screenshot, "_init")
        
        # Initialize History
        self.history = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"GOAL: {user_prompt}"),
                    types.Part.from_bytes(data=screenshot, mime_type="image/jpeg")
                ]
            )
        ]
        
        while True:
            await asyncio.sleep(0.5) 
            
            # THINKING PHASE
            with console.status("[bold purple]Agent is thinking...[/bold purple]", spinner="dots"):
                try:
                    response = await self.agent.think(self.history)
                except Exception as e:
                    console.print(f"[bold red]💥 API Error:[/bold red] {e}")
                    await asyncio.sleep(5)
                    continue

            if not response.candidates:
                console.print("[bold red]❌ Agent returned no content.[/bold red]")
                continue
            
            candidate = response.candidates[0]
            if not candidate.content:
                 console.print(f"[bold red]❌ Empty response. Reason: {candidate.finish_reason}[/bold red]")
                 self.history.append(
                     types.Content(role="user", parts=[types.Part.from_text(text="Empty response. Please try again.")])
                 )
                 continue

            agent_content = candidate.content
            self.history.append(agent_content)
            
            # 1. DISPLAY THOUGHTS
            thoughts = []
            if agent_content.parts:
                for p in agent_content.parts:
                    if p.text:
                        thoughts.append(p.text)
            
            if thoughts:
                self.print_agent_thought("\n".join(thoughts))

            # 2. PARSE TOOLS
            parts = agent_content.parts or []
            tool_calls = [part.function_call for part in parts if part.function_call]
            
            if not tool_calls:
                console.print("[yellow]⚠️ No tools called. Nudging agent...[/yellow]")
                self.history.append(
                    types.Content(
                        role="user", 
                        parts=[types.Part.from_text(text="Please take an action using 'browser_action' or 'task_completed'.")]
                    )
                )
                continue

            # 3. EXECUTE TOOLS
            task_done = False
            for call in tool_calls:
                args_dict = {k: v for k, v in call.args.items()}
                self.print_tool_call(call.name, args_dict)
                
                result_text = ""
                
                # Special handling for tools that require user interaction
                if call.name == "task_completed":
                    result = args_dict.get('result', '')
                    result_text = f"Task Completed: {result}"
                    task_done = True
                    console.print()
                    console.print(Panel(result, title="[bold green]🎉 MISSION ACCOMPLISHED[/bold green]", border_style="bright_green", box=box.HEAVY))
                
                elif call.name == "ask_user":
                    # ASK USER - NO SPINNER
                    question = args_dict.get('question', '')
                    console.print(Panel(f"[bold yellow]❓ Agent Question:[/bold yellow] {question}", border_style="yellow"))
                    answer = console.input("[bold green]Your Answer > [/bold green]")
                    result_text = f"User Answer: {answer}"
                
                elif call.name == "browser_action":
                    # BROWSER ACTION - WITH SPINNER
                    try:
                        with console.status(f"[bold yellow]Executing {call.name}...[/bold yellow]", spinner="clock"):
                            result_text = await self.browser.execute_action(**args_dict)
                    except SecurityRiskError as e:
                        # SECURITY INTERCEPT - NO SPINNER
                        console.print(Panel(
                            f"[bold red]SECURITY ALERT:[/bold red] {str(e)}\n"
                            f"[yellow]Details:[/yellow] {e.risk_details}",
                            title="🛡️ SECURITY INTERCEPT",
                            border_style="red",
                            box=box.HEAVY
                        ))
                        answer = console.input("[bold red]Allow this action? (y/n) > [/bold red]")
                        if answer.lower() == 'y':
                            console.print("[green]Action Authorized. Proceeding...[/green]")
                            with console.status("[bold yellow]Executing (Forced)...[/bold yellow]", spinner="clock"):
                                result_text = await self.browser.execute_action(force=True, **args_dict)
                        else:
                            result_text = "Action blocked by user security policy."
                            console.print("[red]Action Blocked.[/red]")
                
                else:
                    # Generic tools
                    with console.status(f"[bold yellow]Executing {call.name}...[/bold yellow]", spinner="clock"):
                        result_text = f"Unknown tool: {call.name}"

                if not task_done:
                    self.print_tool_result(call.name, result_text)

                # 4. CAPTURE NEW STATE
                self.step_count += 1
                with console.status("[dim cyan]Updating visuals...[/dim cyan]", spinner="simpleDots"):
                    await asyncio.sleep(1.0) # Wait for UI
                    new_screenshot = await self.browser.capture_screenshot()
                    self.save_debug_image(new_screenshot)
                
                # Update History
                self.history.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=call.name,
                                response={"result": result_text}
                            ),
                            types.Part.from_bytes(data=new_screenshot, mime_type="image/jpeg")
                        ]
                    )
                )

                if task_done:
                    break
            
            if task_done:
                break

    async def close(self):
        with console.status("[bold red]Shutting down...[/bold red]"):
            await self.browser.close()

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]❌ GEMINI_API_KEY missing in .env[/bold red]")
        return
    
    orchestrator = Orchestrator(api_key)
    
    console.clear()
    console.print(Panel.fit(
        "[bold white]AgentBrowser[/bold white] [cyan]v2.0[/cyan]\n[dim]Powered by Gemini 2.5 Pro & Flash[/dim]",
        border_style="cyan",
        box=box.DOUBLE
    ))

    try:
        await orchestrator.browser.start()
        
        while True:
            try:
                console.print()
                user_input = console.input("[bold blue]🤖 Command > [/bold blue]")
                if not user_input.strip(): continue
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                await orchestrator.run_task(user_input)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted.[/yellow]")
                continue
            except Exception as e:
                console.print(f"[bold red]Fatal Error:[/bold red] {e}")
                import traceback
                traceback.print_exc()
    finally:
        await orchestrator.close()

if __name__ == "__main__":
    asyncio.run(main())
