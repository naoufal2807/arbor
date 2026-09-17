"""
Router for the Arbor Build API.
Pure routing logic. No I/O, no globals — everything comes in as arguments.
Pipeline: filter (health, constraints) → score (strategy) → rank.
"""
from dataclasses import dataclass

from .registry import BackendSpec
from .stats import BackendStats


@dataclass(frozen=True)
class Constraints:
    max_cost_per_1m: float | None = None
    max_ttft_ms: float | None = None
    min_context_window: int | None = None


@dataclass(frozen=True)
class RoutingDecision:
    winner: str
    fallbacks: list[str]          # rest of the ranking, best-first
    strategy: str
    excluded: dict[str, str]      # backend -> reason (for logging/debug)


class NoBackendFits(Exception):
    def __init__(self, excluded: dict[str, str]):
        self.excluded = excluded
        self.message = "No backend fits the constraints: " + ", ".join(
            f"{b}: {r}" for b, r in excluded.items()
        )
        super().__init__(self.message)


# A scorer takes (spec, stats) and returns a number. LOWER = BETTER.

def _score_cost(spec: BackendSpec, stats: BackendStats) -> float:
    return spec.cost_per_1m_tokens


def _score_latency(spec: BackendSpec, stats: BackendStats) -> float:
    # Unmeasured backend scores worst: never gamble a user request on an
    # unknown when a measured option exists. (Tradeoff: cold start needs
    # a probe mechanism later.)
    return stats.p95_ttft_ms if stats.p95_ttft_ms is not None else float("inf")


SCORERS = {
    "cost": _score_cost,
    "latency": _score_latency,
}


def select(
    specs: list[BackendSpec],
    stats: dict[str, BackendStats],
    constraints: Constraints,
    strategy: str = "cost",
) -> RoutingDecision:
    if strategy not in SCORERS:
        raise ValueError(f"unknown strategy: {strategy!r}")

    excluded: dict[str, str] = {}
    candidates: list[BackendSpec] = []

    # --- PHASE 1: filter — keep reasons for every exclusion ---
    for spec in specs:
        st = stats.get(spec.name)

        if st is None:
            excluded[spec.name] = "no stats"
            continue
        if not st.healthy:
            excluded[spec.name] = "unhealthy"
            continue
        if constraints.max_cost_per_1m is not None and spec.cost_per_1m_tokens > constraints.max_cost_per_1m:
            excluded[spec.name] = "over max_cost"
            continue
        if constraints.min_context_window is not None and spec.context_window < constraints.min_context_window:
            excluded[spec.name] = "context too small"
            continue

        candidates.append(spec)

    if not candidates:
        raise NoBackendFits(excluded)

    # --- PHASE 2: score + rank ---
    scorer = SCORERS[strategy]
    ranked = sorted(candidates, key=lambda s: (scorer(s, stats[s.name]), s.priority, s.name))

    return RoutingDecision(
        winner=ranked[0].name,
        fallbacks=[s.name for s in ranked[1:]],
        strategy=strategy,
        excluded=excluded,
    )