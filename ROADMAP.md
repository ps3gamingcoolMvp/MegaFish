# MegaFish Roadmap

## Current State (v0.2.0) — updated 2026-03-31 after 3 overnight polish sessions

Fully local fork running on Neo4j CE + Ollama. All Zep Cloud dependencies removed. Core pipeline works: upload text → build knowledge graph → entity extraction → simulation → report generation.

### Completed during overnight sessions (not yet in a tagged release)
- [x] CLI `client.py` corrected to match actual Flask API endpoints
- [x] Stale Zep Cloud references removed from progress messages and comments
- [x] Frontend version string and GitHub URL made consistent with package.json / README
- [x] `.gitignore` and `requirements.txt` translated to English comments
- [x] `requests` added to `pyproject.toml` (was missing; CLI uses it)
- [x] Test suite created: 72 tests passing (API, CLI, ontology, SimulationManager, security)
- [x] 6 backend API endpoints fixed: `raise ValueError` → direct 503 response
- [x] Docker Compose networking fixed: backend container now uses `neo4j`/`ollama` hostnames
- [x] Docker Compose health checks added
- [x] `.env.example` completed with all documented variables
- [x] `frontend/.env.example` created for `VITE_API_BASE_URL`
- [x] `megafish update` command hardened to detect both git-clone and install.sh contexts
- [x] `_world_sim_results` dict bounded to prevent unbounded memory growth
- [x] CORS origins now configurable via `CORS_ORIGINS` env var (default `*` for local dev)
- [x] Traceback strings stripped from JSON error responses in non-debug mode
- [x] All 18 report API route functions documented with docstrings
- [x] `console.warn`/`console.error` in MainView.vue replaced with in-UI `addLog()` calls

---

## Near Term

### v0.3.0 — Stability & Python Compatibility
- [ ] Fix `camel-oasis` / `camel-ai` compatibility with Python 3.12+ (currently requires <3.12)
- [ ] Add Docker Compose GPU auto-detection (fallback to CPU-only Ollama)
- [ ] Connection resilience: auto-reconnect to Neo4j on transient failures
- [ ] Add `/api/status` endpoint showing Neo4j connection state, Ollama model availability, and disk usage
- [ ] Structured logging with JSON output option
- [ ] Remove dead code: `Process.vue` (unreachable view) and `generate_python_code()` deprecated function

### v0.4.0 — Search & Retrieval Improvements
- [ ] Tune hybrid search weights (currently 0.7 vector / 0.3 BM25) — make configurable per graph
- [ ] Add graph-aware reranking: boost results connected to the query entity
- [ ] Support multiple embedding models (e.g., mxbai-embed-large, bge-m3 for multilingual)
- [ ] Implement edge-weight decay for temporal relevance in simulations

---

## Mid Term

### v0.5.0 — Multi-Model Support
- [ ] Model router: assign different Ollama models to different tasks (fast model for NER, large model for reports)
- [ ] Support vLLM and llama.cpp as alternative backends alongside Ollama
- [ ] Add model benchmarking tool: compare NER/RE quality across models on the same seed text
- [ ] Quantization-aware config: auto-select context window based on available VRAM

### v0.6.0 — Enhanced Simulation
- [ ] Real-time simulation dashboard with WebSocket updates
- [ ] Agent memory persistence across simulation rounds (currently in-memory)
- [ ] Custom agent archetypes: define personality templates beyond OASIS defaults
- [ ] Multi-language simulation support (agents can interact in different languages)
- [ ] Export simulation transcripts as structured JSON for external analysis

### v0.7.0 — Graph Intelligence
- [ ] Community detection (Louvain/Leiden) to auto-identify entity clusters
- [ ] Graph visualization improvements: force-directed layout, filtering by entity type
- [ ] Temporal graph: track how entity relationships evolve across simulation rounds
- [ ] Graph diff: compare two simulation runs side-by-side

---

## Long Term

### v1.0.0 — Production Ready
- [ ] Authentication & multi-user support
- [ ] Graph versioning: snapshot and restore graph states
- [ ] Plugin system for custom NER extractors, search strategies, and report templates
- [ ] Expand test suite: integration tests against real Neo4j + Ollama (currently all mocked)
- [ ] E2E test: upload → build → simulate → report full pipeline
- [ ] Performance benchmarks: document throughput (texts/min) and latency per hardware tier
- [ ] Helm chart for Kubernetes deployment
- [ ] Production deployment guide: CORS_ORIGINS, FLASK_DEBUG=false, SECRET_KEY rotation

### Beyond v1.0
- [ ] Federation: connect multiple MegaFish instances to share entity knowledge
- [ ] Fine-tuned local models specifically trained for NER/RE on social simulation data
- [ ] Voice-driven interaction: talk to simulation agents via local Whisper + TTS
- [ ] Mobile companion app for monitoring running simulations

---

## Hardware Tiers

| Tier | RAM | GPU VRAM | Recommended Model | Expected Performance |
|------|-----|----------|-------------------|---------------------|
| Minimal | 8 GB | — (CPU only) | qwen2.5:3b | Slow, basic NER quality |
| Light | 16 GB | 6-8 GB | qwen2.5:7b | Usable for small graphs |
| Standard | 32 GB | 12-16 GB | qwen2.5:14b | Good for most use cases |
| Power | 64 GB | 24+ GB | qwen2.5:32b | Full quality, fast |

---

## Contributing

This project is AGPL-3.0 licensed. Contributions welcome — especially around:
- Python 3.12+ compatibility for CAMEL-AI / OASIS
- Additional embedding model support
- Simulation quality improvements
- Documentation and tutorials in English

See [GitHub Issues](https://github.com/nikmcfly/MegaFish/issues) for current tasks.
