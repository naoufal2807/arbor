"""End-to-end test: router decision -> dispatcher -> real Ollama backend -> stats."""
import asyncio
from arbor_build.router import RoutingDecision
from arbor_build.stats import StatsStore
from arbor_build.backends.ollama import OllamaBackend
from arbor_build.dispatcher import dispatch, AllBackendsFailed

MODEL = "model3:0.6b"
#"qwen3:0.6b"  # change to whichever model you want to test

# test recipies 
recipes = [
    "give me a good waffle recipe with coffee taste",
    "give me a good waffle recipe with chocolate taste",
    "give me a good waffle recipe with vanilla taste",
    "give me a good waffle recipe with strawberry taste",
    "give me a good waffle recipe with banana taste",
]
async def main():
    stats = StatsStore(window=5)
    backends = {"ollama": OllamaBackend(model=MODEL)}
    for recipe in recipes:
                #router ouput pre-defined
                decision = RoutingDecision(winner="ollama", fallbacks=[], strategy="cost", excluded={})
                messages = [{"role": "user", "content": recipe}]

                try:
                    response = await dispatch(decision, backends, messages, stats)
                    print("response:", response["content"])
                except AllBackendsFailed as e:
                    print("attempts:", e.attempts)
                print("stats:", stats.snapshot("ollama"))


asyncio.run(main())