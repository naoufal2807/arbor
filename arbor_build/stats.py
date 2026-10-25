"""In-memory stats store for backend health and latency."""
from collections import deque
from dataclasses import dataclass
import statistics


@dataclass
class BackendStats:
    healthy: bool = True
    p95_ttft_ms: float | None = None


class StatsStore:
    def __init__(self, window: int = 20):
        self._window = window
        self._history: dict[str, deque] = {}

    def record_result(self, name: str, ttft_ms: float, ok: bool) -> None:
        if name not in self._history:
            self._history[name] = deque(maxlen=self._window)
        self._history[name].append((ttft_ms, ok))

    def snapshot(self, name: str) -> BackendStats:
        hist = self._history.get(name)
        if not hist:
            return BackendStats()  # cold start

        healthy = hist[-1][1]  # simple rule: last call decides
        latencies = [ttft for ttft, ok in hist if ok]
        p95 = statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 2 else None
        return BackendStats(healthy=healthy, p95_ttft_ms=p95)