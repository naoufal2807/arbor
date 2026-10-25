"""ollama backend for Arbor."""
from ollama import AsyncClient
from .backend import Backend
from typing import AsyncGenerator
from errors import BackendOutputError

class OllamaBackend(Backend):
    def __init__(self, model: str = "gemma2", host: str = "http://localhost:11434"):
        super().__init__(name="ollama")
        self.model = model
        self.client = AsyncClient(host=host)

    async def chat(self, messages: list[dict]) -> dict:
        """Send messages, return a complete response in a common shape."""
        response = await self.client.chat(model=self.model, messages=messages)

        # DEBUG: remove once the 'length' failure is understood
        print("DEBUG done_reason:", response.done_reason)
        print("DEBUG content:", repr(response.message.content))
        print("DEBUG eval_count:", response.eval_count)
        print("DEBUG thinking:", getattr(response.message, "thinking", None))

        if not response.message.content.strip() or response.done_reason != "stop":
            raise BackendOutputError(
                backend=self.name,
                done_reason=response.done_reason,
                content=response.message.content,
            )

        return {
            "content": response.message.content,
            "usage": {
                "prompt_tokens": response.prompt_eval_count,
                "raw": response,
                "completion_tokens": response.eval_count,
                "total_tokens": response.prompt_eval_count + response.eval_count,
            },
        }

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        """Stream messages, yield response chunks as they arrive."""
        async for chunk in await self.client.chat(model=self.model, messages=messages, stream=True):
            yield {"content": chunk.message.content}