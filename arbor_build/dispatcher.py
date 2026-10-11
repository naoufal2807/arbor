"""dispatcher :
    takes a Routingdecision(winner + fallabacks) and a dict of Backend instances,
    actually call the winner, and if it fails, walk the fallback chain recording every real ateempt into
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


def dispatch(routing_decision: RoutingDecision, backends: dict[str, Backend], messages: list[dict], stats_store: StatsStore) -> dict:
    """Dispatch a request to the appropriate backend, handling fallbacks and recording stats."""
    candidates = [routing_decision.winner] + routing_decision.fallbacks
    attempts = {}
    for name in candidates:
        backend = backends[name]
        start = time.monotonic()
        
        try:
            response = backend.chat(messages) # worth check if it is async or not
        except Exception as e:
            # Record the failure and continue to the next candidate
            time_elapsed = time.monotonic() - start
            attempts[name] = str(e)
            stats_store.record_results(name, elapsed=time_elapsed,  ok=False)  # <- check this matches StatsStore's real method name)
            
            