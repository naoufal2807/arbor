# an immutable registry for sharing across requests

from dataclasses import dataclass

@dataclass(frozen=True)
class BackendSpec:
    name: str
    cost_per_1m_tokens: float
    context_window: int
    priority: int  = 0  #tiebreaker: lower number = higher priority
