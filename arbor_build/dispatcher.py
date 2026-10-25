"""dispatcher :
    takes a RoutingDecision (winner + fallbacks) and a dict of Backend instances,
    actually call the winner, and if it fails, walk the fallback chain recording every real attempt into
    StatsStore along the way
    Owns: timing, exception handling, fallback traversal, stats recording. """

import time
from arbor_build.router import RoutingDecision
from arbor_build.stats import StatsStore
from arbor_build.backends.backend import Backend


class AllBackendsFailed(Exception):
    """Raised when all backends have failed to process a request."""
    def __init__(self, attempts: dict[str, str]):
        self.attempts = attempts
        super().__init__(f"All backends failed: {attempts}")


async def dispatch(routing_decision: RoutingDecision, backends: dict[str, Backend], messages: list[dict], stats_store: StatsStore) -> dict:
    """Dispatch a request to the winner, walk the fallback chain on failure, record every attempt."""
    candidates = [routing_decision.winner] + routing_decision.fallbacks
    attempts: dict[str, str] = {}

    for name in candidates:
        backend = backends[name]
        start = time.monotonic()

        try:
            response = await backend.chat(messages)
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            attempts[name] = str(e)
            stats_store.record_result(name, elapsed_ms, ok=False)
            continue

        elapsed_ms = (time.monotonic() - start) * 1000
        stats_store.record_result(name, elapsed_ms, ok=True)
        return response

    raise AllBackendsFailed(attempts)