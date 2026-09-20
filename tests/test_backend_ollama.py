"""
Manual integration check for OllamaBackend.
Requires: `ollama serve` running locally, a model pulled.
Run with: python test_ollama_backend.py
"""
import asyncio
import pytest

pytestmark = pytest.mark.anyio   # tells anyio's plugin to run every test in this file
from arbor_build.backends.ollama import OllamaBackend

MODEL = "qwen3.5:0.8b"   # match whatever `ollama list` actually shows you
MESSAGES = [{"role": "user", "content": "Say hello in exactly 5 words."}]


async def test_check_chat():
    print("=== chat() ===")
    backend = OllamaBackend(model=MODEL)
    result = await backend.chat(MESSAGES)

    # YOURS: print the full result first, look at it with your own eyes
    print(result)

    # YOURS: then add assertions — what MUST be true for this to be correct?
    #   - is result["content"] a non-empty string?
    #   - do the usage numbers look sane (small positive ints, not None)?
    #   - is "raw" present and does it look like the ChatResponse object?
    assert result["content"] and isinstance(result["content"], str)


async def test_check_stream_chat():
    print("=== stream_chat() ===")
    backend = OllamaBackend(model=MODEL)
    chunks = []
    async for chunk in backend.stream_chat(MESSAGES):
        print(chunk)
        chunks.append(chunk)

    # YOURS: what must be true here?
    #   - did you get more than one chunk? (proves it's actually streaming,
    #     not just returning one chunk and stopping)
    #   - does concatenating every chunk's "content" produce a coherent
    #     sentence, roughly matching what chat() alone would produce?
    assert len(chunks) > 1


async def main():
    await check_chat()
    print()
    await check_stream_chat()


if __name__ == "__main__":
    asyncio.run(main())