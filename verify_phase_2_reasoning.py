import asyncio
from agentbrowser.agent.logic import Agent
from unittest.mock import MagicMock, AsyncMock, patch
from google.genai import types

async def verify():
    # We want to see if the agent uses update_plan and save_memory when "thinking"
    # We will mock the AI response to simulate a "reasoning" step.
    
    agent = Agent(api_key="test")
    
    # Simulating First Step: AI decides to create a plan
    mock_call_1 = MagicMock()
    mock_call_1.name = "update_plan"
    mock_call_1.args = {"steps": ["Find price on site A", "Find price on site B", "Compare"], "current_step_index": 0}
    
    mock_response_1 = MagicMock()
    mock_response_1.candidates = [
        MagicMock(content=MagicMock(parts=[
            MagicMock(text=None, function_call=mock_call_1)
        ]))
    ]
    
    with patch.object(agent.client.aio.models, 'generate_content', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response_1
        
        print("Initial prompt: 'Compare prices...'\n")
        response = await agent.think([])
        
        call = response.candidates[0].content.parts[0].function_call
        print(f"Agent decided to: {call.name}({call.args})")
        
        # Now simulate execution of this tool (this happens in Orchestrator usually)
        agent.update_plan(call.args["steps"], call.args["current_step_index"])
        
        # Verify instructions now include the plan
        instr = agent._get_system_instruction()
        print("\nUpdated System Instruction Snippet:")
        print(instr[instr.find("### ТЕКУЩИЙ ПЛАН:"):])
        
        if "0. Find price on site A (ТЕКУЩИЙ)" in instr:
            print("\nPHASE 2 VERIFICATION SUCCESSFUL")
        else:
            print("\nPHASE 2 VERIFICATION FAILED")

if __name__ == "__main__":
    asyncio.run(verify())
