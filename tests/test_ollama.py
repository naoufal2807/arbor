import asyncio
from ollama import AsyncClient

async def test():
    client = AsyncClient()
    response = await client.chat(model="qwen3.5:0.8b", messages=[{"role": "user", "content": "hi"}])
    print(repr(response))
    print("content:", response.message.content)

asyncio.run(test())