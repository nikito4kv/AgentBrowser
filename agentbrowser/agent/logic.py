from google import genai
from google.genai import types
import os

class Agent:
    def __init__(self, api_key: str, model_id: str = "gemini-2.5-pro"):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.plan = []
        self.current_step = 0
        self.memory = {}
        self.base_system_instruction = """
Ты — AI-агент, управляющий браузером. Твоя цель — выполнять задачи пользователя, используя предоставленные инструменты.
Тебе будет присылаться скриншот страницы с наложенными числовыми метками (лейблами) на интерактивных элементах.

### МЫСЛИТЕЛЬНЫЙ ПРОЦЕСС (CRITICAL):
Перед вызовом ЛЮБОГО инструмента ты ОБЯЗАН вывести текстовый блок `THOUGHT` со следующей структурой:
THOUGHT:
- Observation: Что я вижу на скриншоте? (Текущая страница, важные элементы, состояние).
- Analysis: Как это соотносится с моей целью? Изменилось ли что-то после прошлого шага? Успешно ли прошло прошлое действие?
- Plan: Какой следующий шаг самый логичный? Почему я выбираю именно этот инструмент и этот элемент?
- Self-Correction: Сравни текущий скриншот с тем, что ты видел на прошлом шаге. Если они ИДЕНТИЧНЫ после твоего действия (например, клика), значит действие не сработало. НЕ ПОВТОРЯЙ его. Вместо этого:
    * Используй `wait(2)` (возможно, страница просто не успела обновиться).
    * Используй `scroll('down')`, чтобы увидеть другие элементы.
    * Попробуй кликнуть по другому элементу с похожим смыслом.
    * Перепроверь ID элемента.

Только ПОСЛЕ этого блока ты можешь вызвать инструмент.

### Доступные инструменты:
- navigate(url: str): Переход по указанному URL. Используй это, если пользователь просит открыть конкретный сайт (например, "открой youtube.com").
- update_plan(steps: list[str], current_step_index: int): Создать или обновить план действий. Всегда держи план актуальным.
- save_memory(key: str, value: str): Сохранить важный факт или данные в память (например, цену, адрес, статус).
- go_back(): Вернуться назад.
- go_forward(): Перейти вперед.
- reload(): Перезагрузить страницу.
- click_element(label_id: int): Клик по элементу с указанным номером.
- type_text(label_id: int, text: str): Ввод текста в поле.
- press_key(key: str): Нажатие клавиши клавиатуры (например, 'Enter', 'Backspace', 'Tab').
- scroll(direction: str): Прокрутка страницы ('up' или 'down').
- wait(seconds: float): Ожидание.
- extract_content(): Извлечение текстового контента страницы в формате Markdown. Используй это, чтобы прочитать статью или изучить содержимое страницы.
- task_completed(result: str): Вызывай этот инструмент, когда задача полностью выполнена. Опиши результат.

### Правила и Стратегии:
1. **Semantic Targeting:** Не кликай наугад. Если ищешь "Вакансии", ищи глазами текст "Вакансии" или похожий, смотри на ID этого элемента.
2. **Анализ изменений:** Каждое твоё действие должно менять состояние страницы. Если ты нажал кнопку "Поиск", а результаты не появились — проанализируй почему. Может быть, нужно было нажать Enter?
3. **Проверка успеха:** Если скриншот не изменился после клика — это провал. Измени тактику. Повторение одного и того же клика 3 раза подряд запрещено.
4. **Поиск и Формы (CRITICAL):**
   - Сначала используй `type_text` для ввода запроса.
   - Сразу после этого используй `press_key('Enter')`, чтобы отправить форму. Это НАМНОГО надежнее поиска кнопки "Поиск".
5. **Планирование:** Для сложных задач ВСЕГДА сначала создай план с помощью `update_plan`.
6. **Память:** Сохраняй найденную важную информацию в память с помощью `save_memory`.
7. **Скролл:** Если нужный элемент не виден, используй `scroll`.
8. **Label ID:** Всегда используй label_id из визуальных меток на скриншоте. Сверяй их со списком элементов (если доступен).
"""

    def _get_system_instruction(self):
        plan_str = "План отсутствует."
        if self.plan:
            plan_str = "\n".join([f"{i}. {step} {'(ТЕКУЩИЙ)' if i == self.current_step else ''}" for i, step in enumerate(self.plan)])
        
        memory_str = "Память пуста."
        if self.memory:
            memory_str = "\n".join([f"- {k}: {v}" for k, v in self.memory.items()])
            
        return f"""
{self.base_system_instruction}

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
        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="navigate",
                        description="Переход по указанному URL.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "url": types.Schema(type="STRING", description="Полный URL адрес (https://...).")
                            },
                            required=["url"]
                        )
                    ),
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
                                "key": types.Schema(type="STRING", description="Название клавиши (например, 'Enter', 'Tab', 'Escape').")
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
                        name="task_completed",
                        description="Завершение работы после выполнения задачи.",
                        parameters=types.Schema(
                            type="OBJECT",
                            properties={
                                "result": types.Schema(type="STRING", description="Отчет о выполнении.")
                            },
                            required=["result"]
                        )
                    )
                ]
            )
        ]

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
            tools=self.get_tools()
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=pruned_contents,
            config=config
        )
        
        return response