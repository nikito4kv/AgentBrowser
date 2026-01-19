import asyncio
from main import Orchestrator
from unittest.mock import MagicMock

async def verify():
    orch = Orchestrator(api_key="test")
    
    print("Testing update_plan...")
    call_plan = MagicMock()
    call_plan.name = "update_plan"
    call_plan.args = {"steps": ["Navigate to Google", "Search for Conductor", "Click results"], "current_step_index": 0}
    
    await orch.execute_tool(call_plan)
    print(f"Plan: {orch.agent.plan}")
    print(f"Current step index: {orch.agent.current_step}")
    
    print("\nTesting save_memory...")
    call_mem = MagicMock()
    call_mem.name = "save_memory"
    call_mem.args = {"key": "found_docs", "value": "true"}
    
    await orch.execute_tool(call_mem)
    print(f"Memory: {orch.agent.memory}")
    
    if orch.agent.plan == ["Navigate to Google", "Search for Conductor", "Click results"] and orch.agent.memory["found_docs"] == "true":
        print("\nPHASE 1 VERIFICATION SUCCESSFUL")
    else:
        print("\nPHASE 1 VERIFICATION FAILED")

if __name__ == "__main__":
    asyncio.run(verify())
