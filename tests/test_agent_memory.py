import pytest
from agentbrowser.agent.logic import Agent

def test_agent_memory_and_plan_initialization():
    agent = Agent(api_key="test")
    assert agent.plan == []
    assert agent.current_step == 0
    assert agent.memory == {}

def test_agent_update_plan():
    agent = Agent(api_key="test")
    steps = ["Step 1", "Step 2"]
    agent.update_plan(steps, 1)
    assert agent.plan == steps
    assert agent.current_step == 1

def test_agent_save_memory():
    agent = Agent(api_key="test")
    agent.save_memory("key", "value")
    assert agent.memory == {"key": "value"}
