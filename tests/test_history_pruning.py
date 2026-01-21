import pytest
from agentbrowser.agent.logic import Agent
from google.genai import types

def test_prune_history_removes_old_screenshots():
    agent = Agent(api_key="test")
    
    # Создаем историю с 3 сообщениями пользователя, каждое содержит текст и скриншот
    # И 2 сообщениями модели между ними
    
    # 1. User: Task + Screenshot 1
    content1 = types.Content(role="user", parts=[
        types.Part.from_text(text="Task 1"),
        types.Part.from_bytes(data=b"image1", mime_type="image/png")
    ])
    
    # 2. Model: Action
    content2 = types.Content(role="model", parts=[
        types.Part.from_text(text="Action 1")
    ])
    
    # 3. User: Result + Screenshot 2
    content3 = types.Content(role="user", parts=[
        types.Part.from_text(text="Result 1"),
        types.Part.from_bytes(data=b"image2", mime_type="image/png")
    ])
    
    # 4. Model: Action
    content4 = types.Content(role="model", parts=[
        types.Part.from_text(text="Action 2")
    ])
    
    # 5. User: Result + Screenshot 3 (CURRENT)
    content5 = types.Content(role="user", parts=[
        types.Part.from_text(text="Result 2"),
        types.Part.from_bytes(data=b"image3", mime_type="image/png")
    ])
    
    history = [content1, content2, content3, content4, content5]
    
    # Вызываем метод очистки
    pruned_history = agent._prune_history(history)
    
    # Проверяем, что история осталась той же длины
    assert len(pruned_history) == 5
    
    # Проверяем 1-е сообщение: картинки быть не должно
    parts1 = pruned_history[0].parts
    assert len(parts1) == 2
    assert parts1[0].text == "Task 1"
    assert parts1[1].text == "[Image Removed]"
    assert getattr(parts1[1], "inline_data", None) is None
    
    # Проверяем 3-е сообщение: картинки быть не должно
    parts3 = pruned_history[2].parts
    assert len(parts3) == 2
    assert parts3[0].text == "Result 1"
    assert parts3[1].text == "[Image Removed]"
    
    # Проверяем 5-е сообщение (последнее): картинка должна остаться
    parts5 = pruned_history[4].parts
    assert len(parts5) == 2
    assert parts5[0].text == "Result 2"
    # Тут проверяем наличие байтов. В SDK это может быть inline_data или просто bytes при создании
    # Но так как мы создали через from_bytes, проверим, что это НЕ текст-заглушка
    assert parts5[1].text != "[Image Removed]"
