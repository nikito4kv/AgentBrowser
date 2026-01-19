from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Available models:")
for model in client.models.list():
    # В новом SDK используется supported_actions
    if 'generateContent' in model.supported_actions:
        print(f"- {model.name}")
