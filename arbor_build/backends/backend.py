"""A base class for a backend"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class Backend(ABC):
    def __init__(self, name: str):
        self.name = name
    @abstractmethod
    async def chat(self, messages:list[dict]) -> dict:
        """send messages, return a complete response in a common shape"""
        pass

    @abstractmethod
    async def stream_chat(self, messages:list[dict]) -> AsyncGenerator[dict, None]:
        """stream message, yield response chunks as they arrive """
        pass
