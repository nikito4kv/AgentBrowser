from google import genai
from google.genai import types
import os

class Agent:
    def __init__(self, api_key: str, model_id: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.plan = []
        self.current_step = 0
        self.memory = {}
        self.system_instruction = """
Ты — AI-агент, управляющий браузером. Твоя цель — выполнять задачи пользователя, используя предоставленные инструменты.
Тебе будет присылаться скриншот страницы с наложенными числовыми метками (лейблами) на интерактивных элементах.

Доступные инструменты:
- navigate(url: str): Переход по указанному URL. Используй это, если пользователь просит открыть конкретный сайт (например, "открой youtube.com").
- go_back(): Вернуться назад.
- go_forward(): Перерейди вперед.
- reload(): Перезагрузить страницу.
- click_element(label_id: int): Клик по элементу с указанным номером.
- type_text(label_id: int, text: str): Ввод текста в поле.
- scroll(direction: str): Прокрутка страницы ('up' или 'down').
- wait(seconds: float): Ожидание.
- extract_content(): Извлечение текстового контента страницы в формате Markdown. Используй это, чтобы прочитать статью или изучить содержимое страницы.
- task_completed(result: str): Вызывай этот инструмент, когда задача полностью выполнена. Опиши результат.

Правила:
1. Если пользователь дал URL или домен, используй `navigate`. Если запрос поисковый ("найди..."), используй поиск на текущей странице (Google).
2. Анализируй скриншот и выбирай наиболее логичное следующее действие.
3. Если элемент не виден, попробуй проскроллить.
4. Если ты не уверен, что делать, или задача невыполнима, сообщи об этом через текстовый ответ (но старайся использовать инструменты).
5. Всегда используй label_id из визуальных меток на скриншоте.
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

    async def think(self, contents: list):
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            tools=self.get_tools()
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=config
        )
        
        return response