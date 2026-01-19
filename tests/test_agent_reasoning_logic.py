import pytest
from agentbrowser.agent.logic import Agent

def test_system_instruction_is_dynamic():
    agent = Agent(api_key="test")
    
    # Initial state
    instr1 = agent._get_system_instruction()
    assert "План отсутствует." in instr1
    assert "Память пуста." in instr1
    
    # Update plan
    agent.update_plan(["Step 1", "Step 2"], 0)
    instr2 = agent._get_system_instruction()
    assert "0. Step 1 (ТЕКУЩИЙ)" in instr2
    assert "1. Step 2" in instr2
    
    # Save memory
    agent.save_memory("price", "$100")
    instr3 = agent._get_system_instruction()
    assert "- price: $100" in instr3
