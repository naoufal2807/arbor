# stats model
from dataclasses import dataclass 
from collections import deque

@dataclass
class BackendStats:
    healthy: bool = True
    p95_ttft_ms: float | None = None
    
    
class StatsStore:
    def __init__(self, window: int = 100, failure_threshold: int = 5):
        self._stats: dict[str, deque[tuple[float, bool]]] = {}
        self._window = window
        self._failure_threshold = failure_threshold
    
    def record_results(self, backend: str, ttft_ms: float, ok: bool) -> None:
        # record the results of a request to a backend
        if backend not in self._stats:
            self._stats[backend] = deque(maxlen=self._window)
        self._stats[backend].append((ttft_ms, ok))
    
    def snapshot(self) -> dict[str, BackendStats]:
        results = {}
        for backend, samples in self._stats.items():
            latencies = sorted(t for t,ok in samples if ok)
            failures = sum( not ok  for _,ok in samples)
            
            p95 = latencies[int(0.95 * (len(latencies) - 1))] if latencies else None
            healthy = failures < self._failure_threshold
            
            
            results[backend] = BackendStats(healthy=healthy, p95_ttft_ms=p95)
        return results