import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from main import Orchestrator
from google.genai import types

@pytest.mark.asyncio
async def test_orchestrator_recovery_on_empty_response():
    orch = Orchestrator(api_key="test")
    # Подготавливаем историю
    orch.history = [types.Content(role="user", parts=[types.Part.from_text(text="Task")])]
    
    # Мокаем think так, чтобы первый раз он вернул пустой ответ (без candidates),
    # а второй раз - нормальный ответ.
    mock_empty_response = MagicMock()
    mock_empty_response.candidates = []
    
    mock_valid_response = MagicMock()
    mock_call = MagicMock()
    mock_call.name = "task_completed"
    mock_call.args = {"result": "Recovered"}
    mock_valid_response.candidates = [
        MagicMock(content=MagicMock(parts=[
            MagicMock(text=None, function_call=mock_call)
        ]))
    ]
    
    with patch.object(orch.agent, 'think', side_effect=[mock_empty_response, mock_valid_response]) as mock_think:
        with patch.object(orch.browser, 'start', new_callable=AsyncMock):
            with patch.object(orch.browser, 'navigate', new_callable=AsyncMock):
                with patch.object(orch.browser, 'capture_annotated_screenshot', new_callable=AsyncMock) as mock_screenshot:
                    mock_screenshot.return_value = (b"fake_image", [])
                    with patch.object(orch.browser, 'close', new_callable=AsyncMock):
                        # Запускаем run. Он должен войти в цикл, получить пустой ответ, 
                        # откатиться, добавить сообщение об ошибке и попробовать снова.
                        await orch.run("Test Prompt")
    
    # Проверяем, что think был вызван 2 раза
    assert mock_think.call_count == 2
    
    # Проверяем, что в истории появилось сообщение об ошибке
    error_msg = orch.history[-2].parts[0].text # -1 это результат последнего шага, -2 это промпт для повтора
    assert "Предыдущий запрос вызвал ошибку" in error_msg