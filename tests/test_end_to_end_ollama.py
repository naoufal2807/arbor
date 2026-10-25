"""End-to-end test: router decision -> dispatcher -> real Ollama backend -> stats."""
import asyncio
from arbor_build.router import RoutingDecision
from arbor_build.stats import StatsStore
from arbor_build.backends.ollama import OllamaBackend
from arbor_build.dispatcher import dispatch, AllBackendsFailed

MODEL = "qwen3:0.6b"  # change to whichever model you want to test


async def main():
    stats = StatsStore(window=5)
    backends = {"ollama": OllamaBackend(model=MODEL)}

    decision = RoutingDecision(winner="ollama", fallbacks=[], strategy="cost", excluded={})
    messages = [{"role": "user", "content": "Say hello in exactly 3 words."}]

    try:
        response = await dispatch(decision, backends, messages, stats)
        print("response:", response["content"])
    except AllBackendsFailed as e:
        print("attempts:", e.attempts)
    print("stats:", stats.snapshot("ollama"))


asyncio.run(main())