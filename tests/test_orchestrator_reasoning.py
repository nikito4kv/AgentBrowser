import pytest
from unittest.mock import MagicMock
from main import Orchestrator
from google.genai import types

@pytest.mark.asyncio
async def test_orchestrator_executes_reasoning_tools():
    orch = Orchestrator(api_key="test")
    
    # Mock tool call for update_plan
    call_plan = MagicMock()
    call_plan.name = "update_plan"
    call_plan.args = {"steps": ["Step 1"], "current_step_index": 0}
    
    result_plan = await orch.execute_tool(call_plan)
    assert result_plan == "План обновлен"
    assert orch.agent.plan == ["Step 1"]
    
    # Mock tool call for save_memory
    call_mem = MagicMock()
    call_mem.name = "save_memory"
    call_mem.args = {"key": "test_key", "value": "test_value"}
    
    result_mem = await orch.execute_tool(call_mem)
    assert result_mem == "Сохранено в память: test_key = test_value"
    assert orch.agent.memory["test_key"] == "test_value"
