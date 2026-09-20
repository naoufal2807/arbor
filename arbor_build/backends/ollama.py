"""ollama backend for Arbor."""
from pyexpat.errors import messages

from ollama import AsyncClient
from .backend import Backend
from typing import AsyncGenerator

class OllamaBackend(Backend):
    def __init__(self, model: str = "gemma 2", host: str = "http://localhost:11434"):
        super().__init__(name="ollama")
        self.model = model
        self.client = AsyncClient(host=host)
    # chat 
    async def chat(self, messages: list[dict]) -> dict:
        """send messages, return a complete response in a common shape"""
        response = await self.client.chat(model=self.model, messages=messages)
        return {
            "content": response.message.content,
            "usage": {
                "prompt_tokens": response.prompt_eval_count,
                "raw" : response,
                "completion_tokens":  response.prompt_eval_count,  # TODO: check this with other models in ollama, as it may not be accurate for all models
                "total_tokens": response.prompt_eval_count + response.eval_count,
            },
        }
    # stream chat
    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """Stream messages, yield response chunks as they arrive."""
        async for chunk in await self.client.chat(model=self.model, messages=messages, stream=True):
            yield {
            "content": chunk.message.content,
        }


    

