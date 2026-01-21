from google import genai
from google.genai import types
import os
from datetime import datetime
import asyncio
import logging

# Configure logging to file to keep console clean
logging.basicConfig(
    filename='agent_debug.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-pro" 
        self.memory = {}

    def _get_system_instruction(self):
        return f"""
<SYSTEM_CAPABILITY>
* You control a Chromium browser via Playwright automation.
* The current date is {datetime.today().strftime("%A, %B %d, %Y")}.
* You are an expert at navigating the web using visual inputs and DOM accessibility trees.
* **CRITICAL RULE:** You MUST call a tool in every response. Do not output only text. If you are thinking, perform a `wait` or `read_page` action.
</SYSTEM_CAPABILITY>

<TOOL_GUIDANCE>
* **browser_action**: This is your primary tool. It supports:
  - `navigate`: Go to a URL.
  - `left_click`, `right_click`, `double_click`: Click actions. 
    - PREFER using `ref` (from `read_page` or `find`) for reliability.
    - **Occlusion Safety:** If a click fails due to "occlusion", handle the obstructing element (e.g., close the popup) or use `screenshot` to verify.
  - `type`: Type text. Use `ref` to target input fields.
  - `scroll`: Scroll the page.
  - `read_page`: **CRITICAL.** Call this to get the Accessibility Tree (text representation of the DOM) and obtain `ref_id`s (e.g., "ref_42") for elements.
  - `find`: Use AI to find element `ref_id`s by description (e.g., "find the search button").
  - `key`: Press keys (e.g., "Enter", "Escape").
  - `wait`: Use this to explicitly pause if you suspect the page is loading.
  - `screenshot`: Updates your visual context without taking other actions. Use this if you suspect a popup appeared or after a failed action.

* **task_completed**: Call this when you have achieved the goal or cannot proceed.
* **ask_user**: Call this if you need clarification or permission for sensitive actions.
</TOOL_GUIDANCE>

<WORKFLOW>
1. **ANALYZE & WAIT:** Look at the screenshot.
   - Does it look like the previous step? Did the action succeed?
   - Is there a loading spinner or blank section? -> **Call `wait(2)`**. Do NOT click while loading.

2. **LOCATE:**
   - To interact with an element, you need its `ref_id`.
   - **Step A:** Call `read_page` to get the DOM tree.
   - **Step B:** Look for the element in the tree.
   - **Step C:** If the tree is too large or you can't find it, use `browser_action(action='find', text='description')`.
   
3. **ACT:**
   - Once you have the `ref_id` (e.g., "ref_12"), call `browser_action(action='left_click', ref='ref_12')`.
   - If typing, prefer providing the `ref` to ensure the correct field is focused.
   - **Handling Occlusion:** If you get an "occluded" error, identify what is covering the target (often a popup or sticky header) and close it, or try scrolling.

4. **VERIFY (CRITICAL):**
   - After an action, assume it MIGHT fail or take time.
   - Check the new screenshot in the next turn to verify success before moving to the next step.
</WORKFLOW>

<SAFETY_RULES>
* Never delete data, make purchases, or send emails without explicit user confirmation via `ask_user`.
* If you are stuck in a loop, try a different strategy (e.g., navigate by URL instead of clicking).
</SAFETY_RULES>
"""

    def get_tools(self):
        tools = [
            types.FunctionDeclaration(
                name="browser_action",
                description="Interact with the browser (navigate, click, type, scroll, read_page, find).",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "action": types.Schema(
                            type="STRING", 
                            enum=["navigate", "left_click", "right_click", "double_click", "type", "key", "scroll", "read_page", "find", "wait", "screenshot"],
                            description="The action to perform."
                        ),
                        "text": types.Schema(type="STRING", description="URL for navigate, text for type/find, key name for key."),
                        "ref": types.Schema(type="STRING", description="The element reference ID (e.g., 'ref_1') obtained from read_page or find."),
                        "coordinate": types.Schema(
                            type="ARRAY", 
                            items=types.Schema(type="INTEGER"), 
                            description="[x, y] coordinates for click (fallback if ref not found)."
                        ),
                        "scroll_direction": types.Schema(type="STRING", enum=["up", "down", "left", "right"], description="Direction to scroll."),
                        "scroll_amount": types.Schema(type="INTEGER", description="Pixels to scroll."),
                        "duration": types.Schema(type="NUMBER", description="Seconds to wait.")
                    },
                    required=["action"]
                )
            ),
            types.FunctionDeclaration(
                name="task_completed",
                description="Finish the task.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "result": types.Schema(type="STRING", description="Final result or answer.")
                    },
                    required=["result"]
                )
            ),
            types.FunctionDeclaration(
                name="ask_user",
                description="Ask the user a question.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "question": types.Schema(type="STRING", description="Question to ask.")
                    },
                    required=["question"]
                )
            )
        ]
        return [types.Tool(function_declarations=tools)]

    def _prune_history(self, history: list):
        """
        Keeps the history clean. Retains the last screenshot, converts older ones to text placeholders.
        """
        pruned_history = []
        for i, content in enumerate(history):
            new_parts = []
            is_last_message = (i == len(history) - 1)
            
            if content.parts:
                for part in content.parts:
                    has_image = False
                    if hasattr(part, "inline_data") and part.inline_data:
                        has_image = True
                    elif hasattr(part, "file_data") and part.file_data:
                        has_image = True
                    
                    # Also prune huge text blocks (like large DOM dumps) from history if they are old
                    has_large_text = False
                    if part.text and len(part.text) > 20000:
                        has_large_text = True

                    if (has_image or has_large_text) and not is_last_message:
                        label = "[Image Removed]" if has_image else "[Large DOM Tree Removed]"
                        new_parts.append(types.Part.from_text(text=label))
                    else:
                        new_parts.append(part)
            
            pruned_history.append(types.Content(role=content.role, parts=new_parts))
            
        return pruned_history

    async def think(self, contents: list):
        pruned_contents = self._prune_history(contents)
        
        config = types.GenerateContentConfig(
            system_instruction=self._get_system_instruction(),
            tools=self.get_tools(),
            temperature=0.1 
        )
        
        max_retries = 5
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_id,
                    contents=pruned_contents,
                    config=config
                )
                
                # Check for malformed response in candidates
                if response.candidates:
                    candidate = response.candidates[0]
                    # Check if finish reason indicates malformed function call
                    # We check string representation to be safe across library versions
                    finish_reason = str(candidate.finish_reason)
                    if "MALFORMED" in finish_reason:
                        logger.warning(f"Malformed function call detected (Attempt {attempt+1}/{max_retries}): {finish_reason}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(base_delay)
                            continue
                
                return response
                
            except Exception as e:
                error_str = str(e)
                logger.error(f"API Error (Attempt {attempt+1}/{max_retries}): {error_str}")
                
                # Retry on 503 (Unavailable), 429 (Too Many Requests), or "overloaded"
                if any(x in error_str for x in ["503", "429", "overloaded", "UNAVAILABLE"]):
                     if attempt < max_retries - 1:
                        sleep_time = base_delay * (2 ** attempt)
                        await asyncio.sleep(sleep_time)
                        continue
                
                # If it's the last attempt or not a retryable error, re-raise
                if attempt == max_retries - 1:
                    raise e
