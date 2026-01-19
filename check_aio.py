from google import genai
import asyncio

async def check():
    client = genai.Client(api_key="test")
    print(f"Has aio: {hasattr(client, 'aio')}")
    if hasattr(client, 'aio'):
        print(f"aio has models: {hasattr(client.aio, 'models')}")

asyncio.run(check())
