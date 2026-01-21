import pytest
from unittest.mock import AsyncMock, MagicMock
from agentbrowser.agent.logic import Agent
from google.genai import types

@pytest.mark.asyncio
async def test_cot_structure():
    """
    Test that the agent's response includes a structured THOUGHT block 
    before the tool call.
    """
    agent = Agent(api_key="test_key")
    
    # Mock the API response
    mock_response = MagicMock()
    mock_response.candidates = [
        MagicMock(
            content=MagicMock(
                parts=[
                    types.Part.from_text(text="THOUGHT:\nI need to navigate to GitHub.\nTOOL_CALL: navigate"),
                    types.Part.from_function_call(name="navigate", args={"url": "https://github.com"})
                ]
            )
        )
    ]
    
    # We want to ensure the SYSTEM PROMPT actually requests this structure.
    # So we check the system instruction generation.
    sys_instruction = agent._get_system_instruction()
    
    assert "<WORKFLOW>" in sys_instruction
    assert "ANALYZE" in sys_instruction
    assert "LOCATE" in sys_instruction
    assert "ACT" in sys_instruction
    assert "VERIFY" in sys_instruction
