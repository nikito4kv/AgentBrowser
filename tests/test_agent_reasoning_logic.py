import pytest
from datetime import datetime
from agentbrowser.agent.logic import Agent

def test_system_instruction_structure():
    agent = Agent(api_key="test")
    
    instr = agent._get_system_instruction()
    
    # Check for key sections
    assert "<SYSTEM_CAPABILITY>" in instr
    assert "<TOOL_GUIDANCE>" in instr
    assert "<WORKFLOW>" in instr
    assert "<SAFETY_RULES>" in instr
    
    # Check for dynamic date
    current_date = datetime.today().strftime("%A, %B %d, %Y")
    assert current_date in instr
    
    # Check for tool mentions
    assert "browser_action" in instr
    assert "read_page" in instr