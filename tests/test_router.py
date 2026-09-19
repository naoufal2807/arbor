import pytest
from arbor_build.registry import BackendSpec
from arbor_build.stats import BackendStats
from arbor_build.router import select, NoBackendFits, Constraints

SPECS = [
    BackendSpec("ollama",    cost_per_1m_tokens=0.0,  context_window=8000),
    BackendSpec("openai",    cost_per_1m_tokens=0.40, context_window=128000),
    BackendSpec("anthropic", cost_per_1m_tokens=3.00, context_window=200000),
]

def healthy_stats():
    return {s.name: BackendStats(healthy=True, p95_ttft_ms=300.0) for s in SPECS}

def test_cost_strategy_picks_cheapest():
    d = select(SPECS, healthy_stats(), Constraints(), strategy="cost")
    assert d.winner == "ollama"

def test_max_cost_filters_expensive_backends():
    c = Constraints(max_cost_per_1m=1.0)
    d = select(SPECS, healthy_stats(), c, strategy="cost")
    assert "anthropic" not in [d.winner, *d.fallbacks]

def test_unhealthy_backend_is_skipped():
    stats = healthy_stats()
    stats["ollama"].healthy = False
    d = select(SPECS, stats, Constraints(), strategy="cost")
    assert d.winner == "openai"

def test_fallbacks_are_ordered_by_same_score():
    d = select(SPECS, healthy_stats(), Constraints(), strategy="cost")
    assert d.fallbacks == ["openai", "anthropic"]

def test_no_backend_fits_raises_with_reasons():
    c = Constraints(max_cost_per_1m=-1.0)
    with pytest.raises(NoBackendFits) as exc:
        select(SPECS, healthy_stats(), c, strategy="cost")
    assert "ollama" in str(exc.value)

def test_latency_strategy_prefers_fastest():
    stats = healthy_stats()
    stats["openai"].p95_ttft_ms = 90.0
    d = select(SPECS, stats, Constraints(), strategy="latency")
    assert d.winner == "openai"


# cold start problem - no prior stats for a new backend
def test_no_stats_treated_as_eligible():
    d = select(SPECS, {}, Constraints(), strategy="cost")
    assert d.winner == "ollama"
    