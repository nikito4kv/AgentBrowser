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
    
    # Check if 'browser_action' is in the function declarations
    funcs = tools[0].function_declarations
    browser_action = next((f for f in funcs if f.name == "browser_action"), None)
    
    assert browser_action is not None
    
    # Check properties
    props = browser_action.parameters.properties
    assert "action" in props
    assert "text" in props
    
    # Check if 'navigate' is an allowed action
    actions = props["action"].enum
    assert "navigate" in actions
    assert "read_page" in actions
