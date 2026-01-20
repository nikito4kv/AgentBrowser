from google import genai
from google.genai import types
import os

class Agent:
    def __init__(self, api_key: str, role: str = "actor"):
        self.client = genai.Client(api_key=api_key)
        self.role = role.lower()
        self.plan = []
        self.current_step = 0
        self.memory = {}
        
        # Role-based configuration
        if self.role == "planner":
            self.model_id = "gemini-2.5-pro"
        elif self.role == "actor":
            self.model_id = "gemini-2.5-flash"
        else:
            raise ValueError(f"Unknown role: {role}")

        self.system_instruction_template = self._get_role_system_instruction()

    def _get_role_system_instruction(self):
        if self.role == "planner":
            return """
You are the **Planner Agent**. Your goal is to architect and control the execution of a user's task in a web browser.
You do NOT interact with the browser directly. You act by giving clear, step-by-step INSTRUCTIONS to the **Actor Agent**.

### YOUR RESPONSIBILITIES:
1. **Analyze:** Carefully examine the current screenshot and conversation history. Identify the user's ultimate goal.
2. **Evaluate:** Check if the previous action was successful. Did the page change? Did we get closer to the goal?
3. **Plan:** Decide the immediate next step.
4. **Instruct:** Issue a precise instruction for the Actor using the `delegate_to_actor` tool.

### CRITICAL RULES:
1. **IMMUTABLE GOAL:** Never lose sight of the user's original request. If the user asked for "Hot Dog", do not search for "Milk".
2. **USE THE 'ENTER' KEY:** When searching or submitting forms, ALWAYS instruct the Actor to "Press Enter" after typing. DO NOT ask to click the "Search" icon/button, as it is often misidentified (e.g., as Image Search).
   - BAD: "Click the search button."
   - GOOD: "Type 'query' into the search box and press Enter."
3. **NO HALLUCINATIONS:** Only refer to elements that are explicitly visible and labeled with a numeric ID on the screenshot. If you don't see it, don't invent it. Use `scroll` to find it.
4. **VERIFY BEFORE COMPLETING:** Do not call `task_completed` until you visually see the result.
   - **PARANOIA LEVEL: HIGH.** If the screenshot looks identical to the previous step, the action FAILED. Do not assume success.
   - If you asked to search, verify you see "Results for..." or a list of links. If you still see the homepage, RETRY with `press_key('Enter')` or click the button.
5. **LANGUAGE:** Think in English for better logic, but you can output the final instruction in the user's language if needed.

### OUTPUT FORMAT:
- First, provide your **THOUGHTS** (Observation, Analysis, Plan).
- Then, call the `delegate_to_actor` tool with the instruction.
"""
        elif self.role == "actor":
            return """
You are the **Actor Agent**. Your job is to execute the specific INSTRUCTION provided by the Planner.
You are the "hands" of the system.

### YOUR RESPONSIBILITIES:
1. Read the `INSTRUCTION` from the Planner.
2. Look at the screenshot and find the numeric ID of the element mentioned in the instruction.
3. Call the appropriate tool(s). **You can call multiple tools in sequence if needed.**
   - Example: If instruction is "Type 'query' and press Enter", you must call `type_text` AND `press_key` in the same turn.

### RULES:
- **OBEY:** Do exactly what the Planner asked. Do not deviate.
- **PRECISION:** Use the exact `label_id` from the screenshot.
- **CHAINING:** If the instruction implies submitting a form (e.g. "Search", "Login", "Enter"), ALWAYS follow `type_text` with `press_key('Enter')` unless there is a clear "Submit" button to click.
"""
        return ""

    def _get_system_instruction(self):
        # Base instruction + dynamic state
        base = self.system_instruction_template
        
        plan_str = "План отсутствует."
        if self.plan:
            plan_str = "\n".join([f"{i}. {step} ({'ТЕКУЩИЙ' if i == self.current_step else ''})" for i, step in enumerate(self.plan)])
        
        memory_str = "Память пуста."
        if self.memory:
            memory_str = "\n".join([f"- {k}: {v}" for k, v in self.memory.items()])
            
        return f"""
{base}

### ТЕКУЩИЙ ПЛАН:
{plan_str}

### ПАМЯТЬ (СОХРАНЕННЫЕ ФАКТЫ):
{memory_str}
"""

    def update_plan(self, steps: list, current_step: int):
        self.plan = steps
        self.current_step = current_step

    def save_memory(self, key: str, value: str):
        self.memory[key] = value

    def get_tools(self):
        # Common tools
        common_tools = []
        
        # Planner Tools (High-level control)
        planner_tools = [
            types.FunctionDeclaration(
                name="update_plan",
                description="Создать или обновить план действий.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "steps": types.Schema(type="ARRAY", items=types.Schema(type="STRING"), description="Список шагов."),
                        "current_step_index": types.Schema(type="INTEGER", description="Индекс текущего шага (0-based).")
                    },
                    required=["steps", "current_step_index"]
                )
            ),
            types.FunctionDeclaration(
                name="save_memory",
                description="Сохранить важный факт или данные в память.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "key": types.Schema(type="STRING", description="Ключ для сохранения."),
                        "value": types.Schema(type="STRING", description="Значение для сохранения.")
                    },
                    required=["key", "value"]
                )
            ),
            types.FunctionDeclaration(
                name="ask_user",
                description="Спросить пользователя о чем-то или запросить подтверждение.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "question": types.Schema(type="STRING", description="Вопрос к пользователю.")
                    },
                    required=["question"]
                )
            ),
            types.FunctionDeclaration(
                name="task_failed",
                description="Сообщить о невозможности выполнить задачу.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "reason": types.Schema(type="STRING", description="Причина неудачи.")
                    },
                    required=["reason"]
                )
            ),
            types.FunctionDeclaration(
                name="task_completed",
                description="Завершение работы после выполнения задачи.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "result": types.Schema(type="STRING", description="Отчет о выполнении.")
                    },
                    required=["result"]
                )
            ),
            types.FunctionDeclaration(
                name="delegate_to_actor",
                description="Передать инструкцию Исполнителю (Actor) для выполнения действия в браузере.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "instruction": types.Schema(type="STRING", description="Четкая, пошаговая инструкция для Actor'а. Например: 'Введи текст X в поле Y' или 'Кликни на кнопку Z'.")
                    },
                    required=["instruction"]
                )
            )
        ]

        # Actor Tools (Browser Interaction)
        actor_tools = [
            types.FunctionDeclaration(
                name="navigate",
                description="Переход по указанному URL.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "url": types.Schema(type="STRING", description="Полный URL адрес (https://...)." )
                    },
                    required=["url"]
                )
            ),
            types.FunctionDeclaration(
                name="go_back",
                description="Вернуться на предыдущую страницу.",
                parameters=types.Schema(type="OBJECT", properties={})
            ),
            types.FunctionDeclaration(
                name="go_forward",
                description="Перейти на следующую страницу (если был возврат).",
                parameters=types.Schema(type="OBJECT", properties={})
            ),
            types.FunctionDeclaration(
                name="reload",
                description="Перезагрузить текущую страницу.",
                parameters=types.Schema(type="OBJECT", properties={})
            ),
            types.FunctionDeclaration(
                name="click_element",
                description="Клик по элементу с указанным визуальным номером ID.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "label_id": types.Schema(type="INTEGER", description="ID из визуальной метки на скриншоте.")
                    },
                    required=["label_id"]
                )
            ),
            types.FunctionDeclaration(
                name="type_text",
                description="Ввод текста в поле с указанным визуальным номером ID.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "label_id": types.Schema(type="INTEGER", description="ID из визуальной метки на скриншоте."),
                        "text": types.Schema(type="STRING", description="Текст для ввода.")
                    },
                    required=["label_id", "text"]
                )
            ),
            types.FunctionDeclaration(
                name="press_key",
                description="Нажатие клавиши клавиатуры.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "key": types.Schema(type="STRING", description="Название клавиши (например, 'Enter', 'Backspace', 'Tab').")
                    },
                    required=["key"]
                )
            ),
            types.FunctionDeclaration(
                name="scroll",
                description="Прокрутка страницы вверх или вниз.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "direction": types.Schema(type="STRING", enum=["up", "down"], description="Направление прокрутки.")
                    },
                    required=["direction"]
                )
            ),
            types.FunctionDeclaration(
                name="wait",
                description="Ожидание в течение нескольких секунд.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "seconds": types.Schema(type="NUMBER", description="Количество секунд.")
                    },
                    required=["seconds"]
                )
            ),
            types.FunctionDeclaration(
                name="extract_content",
                description="Извлечь текстовое содержимое текущей страницы в формате Markdown.",
                parameters=types.Schema(type="OBJECT", properties={})
            ),
            types.FunctionDeclaration(
                name="get_element_details",
                description="Получить подробные атрибуты элемента (ссылку, текст, title) перед кликом.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "label_id": types.Schema(type="INTEGER", description="ID элемента.")
                    },
                    required=["label_id"]
                )
            )
        ]

        if self.role == "planner":
            return [types.Tool(function_declarations=planner_tools)]
        elif self.role == "actor":
            # Actor might also need task_failed if it cannot perform action physically
            # But let's keep it pure. Actually, let's give Actor a way to report failure.
            # We can reuse task_failed for Actor to say "I can't click".
            return [types.Tool(function_declarations=actor_tools + [planner_tools[-2]])] # Adding task_failed
        
        return []

    def _prune_history(self, history: list):
        """
        Удаляет старые скриншоты из истории, оставляя только текстовые пометки.
        Оставляет скриншот в последнем сообщении (если он есть), чтобы агент видел текущее состояние.
        """
        pruned_history = []
        for i, content in enumerate(history):
            new_parts = []
            is_last_message = (i == len(history) - 1)
            
            if content.parts:
                for part in content.parts:
                    # Проверяем наличие данных изображения
                    has_image = False
                    if hasattr(part, "inline_data") and part.inline_data:
                        has_image = True
                    elif hasattr(part, "file_data") and part.file_data:
                        has_image = True
                    
                    # Проверяем наличие длинного текста (например, результат скрапинга)
                    has_large_text = False
                    if part.text and len(part.text) > 500:
                        has_large_text = True

                    # Если есть картинка или большой текст и это НЕ последнее сообщение -> заменяем на заглушку
                    if (has_image or has_large_text) and not is_last_message:
                        label = "[Скриншот удален]" if has_image else "[Текст удален для экономии контекста]"
                        new_parts.append(types.Part.from_text(text=label))
                    else:
                        new_parts.append(part)
            
            pruned_history.append(types.Content(role=content.role, parts=new_parts))
            
        return pruned_history

    async def think(self, contents: list):
        # Очищаем историю от старых скриншотов
        pruned_contents = self._prune_history(contents)
        
        config = types.GenerateContentConfig(
            system_instruction=self._get_system_instruction(),
            tools=self.get_tools(),
            temperature=0.0  # Делаем модель максимально детерминированной
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=pruned_contents,
            config=config
        )
        
        return response
