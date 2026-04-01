<div align="center">

<img src="./static/image/megafish-banner.png" alt="MegaFish" width="100%"/>

# MegaFish

**Fully local multi-agent social simulation — no cloud APIs required. English UI.**

*Upload a document. Watch hundreds of AI agents argue about it on the internet.*

[![GitHub Stars](https://img.shields.io/github/stars/ps3gamingcoolMvp/MegaFish?style=flat-square&color=ff2222)](https://github.com/ps3gamingcoolMvp/MegaFish/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/ps3gamingcoolMvp/MegaFish?style=flat-square)](https://github.com/ps3gamingcoolMvp/MegaFish/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](./LICENSE)

</div>

## Install

**macOS / Linux**
```bash
curl -fsSL https://megafish.sh/install.sh | bash
```

**Windows (PowerShell)**
```powershell
irm https://megafish.sh/install.ps1 | iex
```

Then run:
```bash
megafish
```

## What is this?

MegaFish is a multi-agent simulation engine: upload any document (press release, policy draft, financial report), and it generates hundreds of AI agents with unique personalities that simulate the public reaction on social media. Posts, arguments, opinion shifts — hour by hour.

Everything runs on your machine. No cloud API keys. No data leaving your hardware.

This is a fork of [the original MegaFish](https://github.com/666ghj/MegaFish) (Chinese market, cloud APIs) rebuilt to be **fully local and fully English**:

| Original MegaFish | This fork |
|---|---|
| Chinese UI | **English UI** (1,000+ strings translated) |
| Zep Cloud (graph memory) | **Neo4j Community Edition 5.18** |
| DashScope / OpenAI API | **Ollama** (qwen2.5, llama3, etc.) |
| Cloud API keys required | **Zero cloud dependencies** |

## Workflow

1. **Graph Build** — Extracts entities (people, companies, events) and relationships from your document. Builds a knowledge graph with memory via Neo4j.
2. **Env Setup** — Generates hundreds of agent personas, each with unique personality, opinion bias, reaction speed, influence level, and memory of past events.
3. **Simulation** — Agents interact on simulated social platforms: posting, replying, arguing, shifting opinions. Tracks sentiment evolution, topic propagation, and influence dynamics in real time.
4. **Report** — A ReportAgent analyzes the simulation, interviews focus groups of agents, searches the knowledge graph for evidence, and generates a structured analysis.
5. **Interaction** — Chat with any agent from the simulated world. Ask them why they posted what they posted. Full memory and personality persists.

## Screenshot

<div align="center">
<img src="./static/image/megafish-screenshot.jpg" alt="MegaFish — English UI" width="100%"/>
</div>

## Manual Install

### Prerequisites

- Docker & Docker Compose (recommended), **or**
- Python 3.11+, Node.js 18+, Neo4j 5.18+, Ollama

### Option A: Docker (easiest)

```bash
git clone https://github.com/ps3gamingcoolMvp/MegaFish.git
cd MegaFish
cp .env.example .env

# Start all services (Neo4j, Ollama, MegaFish)
docker compose up -d

# Pull the required models into Ollama
docker exec megafish-ollama ollama pull qwen2.5:32b
docker exec megafish-ollama ollama pull nomic-embed-text
```

Open `http://localhost:3000` — that's it.

### Option B: Manual

**1. Start Neo4j**

```bash
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/megafish \
  neo4j:5.18-community
```

**2. Start Ollama & pull models**

```bash
ollama serve &
ollama pull qwen2.5:32b      # LLM (or qwen2.5:14b for less VRAM)
ollama pull nomic-embed-text  # Embeddings (768d)
```

**3. Configure & run backend**

```bash
cp .env.example .env
# Edit .env if your Neo4j/Ollama are on non-default ports

cd backend
pip install -r requirements.txt
python run.py
```

**4. Run frontend**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## CLI

The bootstrap installer adds a `megafish` command:

```
megafish           — start MegaFish
megafish stop      — stop all services
megafish status    — check service health
megafish update    — pull latest version
megafish uninstall — remove MegaFish
megafish help      — show commands
```

## Configuration

All settings are in `.env` (copy from `.env.example`):

```bash
# LLM — points to local Ollama (OpenAI-compatible API)
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=qwen2.5:32b

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=megafish

# Embeddings
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
```

Works with any OpenAI-compatible API — swap Ollama for Claude, GPT, or any other provider by changing `LLM_BASE_URL` and `LLM_API_KEY`.

## Architecture

```
┌─────────────────────────────────────────┐
│              Flask API                   │
│  graph.py  simulation.py  report.py     │
└──────────────┬──────────────────────────┘
               │ app.extensions['neo4j_storage']
┌──────────────▼──────────────────────────┐
│           Service Layer                  │
│  EntityReader  GraphToolsService         │
│  GraphMemoryUpdater  ReportAgent         │
└──────────────┬──────────────────────────┘
               │ storage: GraphStorage
┌──────────────▼──────────────────────────┐
│         GraphStorage (abstract)          │
│              │                            │
│    ┌─────────▼─────────┐                │
│    │   Neo4jStorage     │                │
│    │  ┌───────────────┐ │                │
│    │  │ EmbeddingService│ ← Ollama       │
│    │  │ NERExtractor   │ ← Ollama LLM   │
│    │  │ SearchService  │ ← Hybrid search │
│    │  └───────────────┘ │                │
│    └───────────────────┘                │
└─────────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │  Neo4j CE   │
        │  5.18       │
        └─────────────┘
```

- `GraphStorage` is an abstract interface — swap Neo4j for any graph DB by implementing one class
- Dependency injection via Flask `app.extensions` — no global singletons
- Hybrid search: 0.7 × vector similarity + 0.3 × BM25 keyword search

## Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 16 GB | 32 GB |
| VRAM (GPU) | 10 GB (14b model) | 24 GB (32b model) |
| Disk | 20 GB | 50 GB |
| CPU | 4 cores | 8+ cores |

CPU-only mode works but is significantly slower. For lighter setups, use `qwen2.5:14b` or `qwen2.5:7b`.

## Use Cases

- **PR crisis testing** — simulate the public reaction to a press release before publishing
- **Trading signal generation** — feed financial news and observe simulated market sentiment
- **Policy impact analysis** — test draft regulations against simulated public response
- **Creative experiments** — someone fed it a classical Chinese novel with a lost ending; the agents wrote a narratively consistent conclusion

## License

AGPL-3.0 — same as the original MegaFish project. See [LICENSE](./LICENSE).

## Credits & Attribution

Fork of [MegaFish](https://github.com/666ghj/MegaFish) by [666ghj](https://github.com/666ghj), originally supported by [Shanda Group](https://www.shanda.com/). Simulation engine powered by [OASIS](https://github.com/camel-ai/oasis) from the CAMEL-AI team.

**Changes in this fork:**
- Backend migrated from Zep Cloud to local Neo4j CE 5.18 + Ollama
- Entire frontend translated from Chinese to English (20 files, 1,000+ strings)
- Bootstrap installer (`megafish` CLI) for macOS, Linux, and Windows
- All Zep references replaced with Neo4j across UI and backend
