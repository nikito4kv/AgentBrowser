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
            self.model_id = "gemini-2.5-pro" # Возвращаем Pro модель для глубокого планирования
        elif self.role == "actor":
            self.model_id = "gemini-2.5-flash"
        else:
            raise ValueError(f"Unknown role: {role}")

        self.system_instruction_template = self._get_role_system_instruction()

    def _get_role_system_instruction(self):
        if self.role == "planner":
            return """
Ты — Planner Agent (Архитектор). Твоя задача — стратегическое управление.
Ты НЕ кликаешь по кнопкам. Ты управляешь Actor'ом.

### ГЛАВНАЯ ЦЕЛЬ (GLOBAL GOAL):
Твоя задача — выполнить просьбу пользователя **минимальным количеством шагов**.

### АЛГОРИТМ РАБОТЫ (ОБЯЗАТЕЛЬНО):
На каждом шаге ты должен пройти этот чек-лист в мыслях:

1. **АНАЛИЗ:** Что изменилось на экране? (Был поиск -> появились результаты).
2. **ПРОВЕРКА ЦЕЛИ:** 
   - Если цель "Найти информацию" (например, "какой заголовок?", "сколько стоит?") И эта информация видна на экране -> **ТВОЙ ХОД ЗАВЕРШЕН**. Вызывай `task_completed` с ответом. НЕ КЛИКАЙ по ссылке, если ответ уже виден.
   - Если цель "Перейти" или "Купить" -> Ищи нужный элемент и давай инструкцию Actor'у.
3. **ПЛАН:** Если цель не достигнута, какой следующий шаг? (Ввести текст? Нажать кнопку? Проскроллить?).

### ПРАВИЛА ИНСТРУКЦИЙ (ДЛЯ ACTOR):
- Actor тупой. Ему нужны четкие ID.
- **ПОИСК:** Инструкция: "Введи 'текст' в поле ID X и нажми Enter". (Actor сам поймет, что это `type` + `press`).
- **КЛИК:** Инструкция: "Кликни на ID Y".

### ФОРМАТ ВЫВОДА (В МЫСЛЯХ):
- STATUS: (Что мы сделали?)
- NEXT ACTION: (Что делаем сейчас?)
- REASON: (Почему?)

6. **ОЖИДАНИЕ:** Если страница пустая ("Нет видимых элементов") или явно загружается — используй инструмент `wait(2)`. Не выдумывай действия.

Твои инструменты:
- `delegate_to_actor`: Отправить команду Исполнителю.
- `wait`: Подождать загрузки.
- `update_plan`: Обновить список шагов.
"""
        elif self.role == "actor":
            return """
Ты — Actor Agent (Исполнитель). Твоя задача — выполнять конкретные инструкции от Planner'а.
Ты отвечаешь за точность кликов и ввода текста.

### ПРАВИЛА:
1. **ИСПОЛНЕНИЕ:** Делай ровно то, что просит Planner.
2. **ЦЕПОЧКА ДЕЙСТВИЙ:** Ты можешь вызвать несколько инструментов сразу (например, `type_text` и затем `press_key('Enter')`), если инструкция это подразумевает.
3. **ТОЧНОСТЬ:** Используй правильные ID элементов из визуальных меток на скриншоте.

Твои инструменты:
- `click_element`, `type_text`, `press_key`, `scroll`, `wait`, `navigate`, `extract_content`, `get_element_details`.
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
                name="wait",
                description="Ожидание в течение нескольких секунд. Используй, если страница пустая или загружается.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "seconds": types.Schema(type="NUMBER", description="Количество секунд.")
                    },
                    required=["seconds"]
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
