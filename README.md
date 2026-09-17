<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/arbor-logo-dark.svg">
    <img src="assets/arbor-logo-full.svg" alt="Arbor — route inference intelligently" width="440">
  </picture>
</p>

<p align="center">
  <b>An open-source inference gateway. Send one request — Arbor routes it to the cheapest, fastest, or best LLM backend for the job.</b>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#roadmap">Roadmap</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

## Why Arbor?

If you use more than one LLM backend — a local Ollama model, OpenAI, Anthropic — you are probably:

- **Hand-writing routing logic** (`if task == "classification": use_mistral()`) in every project
- **Overpaying**, because requests that a free local 7B could handle go to a paid API
- **Blind to costs** — no idea what each request, feature, or user actually costs you
- **One outage away from downtime** — no fallback when a provider goes down

Arbor is a single gateway in front of all your backends. Your app speaks the OpenAI API format it already knows; Arbor makes the routing decision, enforces your cost and latency constraints, falls back on failure, and tells you exactly what every request cost.

```
your app ──▶ Arbor ──▶ Ollama (free)      ← chosen: fits budget, healthy
                   ├──▶ OpenAI            ← fallback
                   └──▶ Anthropic         ← filtered out: over budget
```

## Quick start

> **Status: early development (v0.x).** APIs will change. Star the repo to follow along.

### 1. Install

```bash
git clone https://github.com/naoufal2807/arbor.git
cd arbor
pip install -e .
```

### 2. Configure backends

`config/backends.yaml`:

```yaml
backends:
  ollama:
    type: ollama
    host: http://localhost:11434
    model: mistral:7b
    cost_per_1m_tokens: 0.0
  openai:
    type: openai
    model: gpt-4o-mini
    api_key: ${OPENAI_API_KEY}
    cost_per_1m_tokens: 0.40

routing:
  default_strategy: cost        # cost | latency | quality
  fallback_chain: [ollama, openai]
```

### 3. Run the gateway

```bash
uvicorn arbor.main:app --port 8000
```

### 4. Send a request

Arbor speaks the OpenAI wire format, so any OpenAI-compatible client works — just point it at the gateway:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Where is my order #4521?"}],
    "max_cost": 0.001,
    "optimize_for": "cost"
  }'
```

Response — standard OpenAI shape, plus Arbor's metadata telling you what happened:

```json
{
  "choices": [{ "message": { "role": "assistant", "content": "..." } }],
  "x_gateway": {
    "backend": "ollama",
    "cost": 0.0,
    "ttft_ms": 342,
    "cache_hit": false,
    "fallback": false
  }
}
```

## How it works

Every request passes through a five-stage pipeline:

```
validate ──▶ cache ──▶ route ──▶ optimize ──▶ dispatch
                │                                │
            hit? return                 retries · fallback chain
            ($0, ~2ms)                  circuit breakers
```

1. **Validate** — schema, size limits, constraint sanity
2. **Cache** — identical recent requests return instantly at zero cost (LRU + TTL)
3. **Route** — filter backends by health and constraints (`max_cost`, `max_ttft_ms`, context window), then score survivors by strategy. Strategies are pluggable scoring functions
4. **Optimize** — prompt compression and context dedup shrink the token count before it costs you money
5. **Dispatch** — call the winner with a shared timeout budget; on failure, retry once, then walk the fallback chain. Repeated failures open a per-backend circuit breaker, which feeds back into routing health — the system routes around outages and heals itself

Every request is appended to a JSONL log (backend used, cost, latency, cache/fallback flags) and exported as Prometheus metrics.

### Routing strategies

| Strategy  | Picks                                   | Use when                          |
|-----------|-----------------------------------------|-----------------------------------|
| `cost`    | Cheapest backend that fits constraints  | High-volume, cost-sensitive tasks |
| `latency` | Lowest p95 TTFT                         | User-facing, real-time UX         |
| `quality` | Highest capability tier within budget   | Reasoning-heavy tasks             |

Adding a strategy is one scoring function — see [Contributing](#contributing).

## Configuration

All configuration lives in YAML — no code changes to add a backend.

| File                   | Purpose                                      |
|------------------------|----------------------------------------------|
| `config/backends.yaml` | Backend definitions, pricing, fallback chain |
| `config/gateway.yaml`  | Server, cache TTL, log paths, timeouts       |

Supported backends:

- [x] **Ollama** (local, free)
- [x] **OpenAI** (API)
- [ ] **Anthropic** (API) — in progress
- [ ] **vLLM** (self-hosted) — planned
- [ ] Any OpenAI-compatible endpoint — planned

## Deployment

```bash
docker compose up
```

Ships with a `docker-compose.yml` that runs Arbor + Ollama side by side. Health check at `/healthz`, Prometheus metrics at `/metrics`.

## Roadmap

- [x] OpenAI-compatible HTTP API
- [x] Multi-backend routing (cost / latency / quality)
- [x] Response caching + request dedup
- [ ] Fallback chains + circuit breakers
- [ ] Request logging + cost dashboard
- [ ] Prompt compression
- [ ] Request batching
- [ ] Streaming support
- [ ] A/B testing between routing strategies

## Contributing

Issues, PRs, and feedback are welcome — especially new backends and routing strategies.

```bash
git clone https://github.com/<you>/arbor.git
cd arbor
pip install -e ".[dev]"
pytest
```

**Add a backend:** subclass `Backend` in `arbor/backends/`, implement `chat()` and `stream_chat()`, register it in the config schema.

**Add a routing strategy:** write one scoring function in `arbor/router.py` and add it to the `SCORERS` dict.

## License

MIT

