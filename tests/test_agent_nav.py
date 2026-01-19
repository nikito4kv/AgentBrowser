import pytest
from unittest.mock import MagicMock, patch
from agentbrowser.agent.logic import Agent

@pytest.mark.asyncio
async def test_agent_chooses_navigate():
    # We are testing if the agent CAN emit 'navigate' tool call.
    # Since we don't have a real model connected in unit tests that guarantees behavior,
    # we verify that the tool definition exists in the config sent to the model.
    
    agent = Agent(api_key="test")
    tools = agent.get_tools()
    
    # Check if 'navigate' is in the function declarations
    funcs = tools[0].function_declarations
    nav_func = next((f for f in funcs if f.name == "navigate"), None)
    back_func = next((f for f in funcs if f.name == "go_back"), None)
    
    assert nav_func is not None
    assert back_func is not None
    assert "url" in nav_func.parameters.properties
