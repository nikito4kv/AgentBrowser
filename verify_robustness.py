import asyncio
import os
import sys
from dotenv import load_dotenv
from main import Orchestrator

load_dotenv()

async def run_test():
    file_path = os.path.abspath("test_popup.html")
    url = f"file:///{file_path.replace(os.sep, '/')}"
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found")
        return

    print(f"--- Starting Robustness Verification ---")
    print(f"Target URL: {url}")
    print("Goal: Agent should close the popup FIRST, then click 'CLICK ME FOR SUCCESS'.")
    
    orchestrator = Orchestrator(api_key)
    
    try:
        # Задача сформулирована так, чтобы агент сам догадался закрыть попап
        await asyncio.wait_for(
            orchestrator.run(f"Navigate to {url}. Your goal is to click the 'CLICK ME FOR SUCCESS' button. Notice any popups blocking your view."),
            timeout=120
        )
    except asyncio.TimeoutError:
        print("\n[TEST END] Timeout reached.")
    except Exception as e:
        print(f"\n[TEST ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
