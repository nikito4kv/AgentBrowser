import asyncio
import os
from dotenv import load_dotenv
from main import Orchestrator

load_dotenv()

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment variables.")
        return

    # Use a specific instruction to test reasoning
    instruction = "Перейди на github.com, найди репозиторий 'AutoGPT' и скажи мне, сколько у него звезд."
    
    print(f"Starting reproduction script with instruction: '{instruction}'")
    
    orchestrator = Orchestrator(api_key=api_key)
    # We will manually run the loop for a few steps or until completion
    # await orchestrator.start() # Orchestrator.start() doesn't exist, run() handles startup
    
    # Inject the initial task
    print("Running orchestrator...")
    await orchestrator.run(instruction)

if __name__ == "__main__":
    asyncio.run(main())
