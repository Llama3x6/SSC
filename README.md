# Sentient Supply Chain (SSC)

A mock ERP system with an AI agent layer, built to demonstrate the translation 
of supply chain operations logic into a well-engineered digital system.

## What it is

SSC simulates the core data model and workflows of an ERP system — inventory, 
suppliers, and purchase orders — exposed via a REST API. On top of that, a 
LangGraph agent monitors stock levels, proposes reorders, and requires human 
approval before committing to the system. Three LLM-augmented scripts provide 
operational intelligence: a shift report, a supplier selection narrative, and 
a geopolitical risk digest.

## Why it exists

Most AI demos are disconnected from real operational context. SSC is built 
around a concrete business problem: a supply chain operator needs to know what 
to reorder, from whom, and whether geopolitical conditions put their suppliers 
at risk. The agent layer is deliberately minimal — LLMs are used only where 
judgment is required. Deterministic logic stays deterministic.

## Architecture

```
ERP API (FastAPI)
├── Router layer     — HTTP translation, status codes, no business logic
├── Service layer    — Business rules, domain exceptions
└── Repository layer — Data access only, swappable (in-memory → SQLAlchemy)

Agent Layer (LangGraph)
├── ReorderAgent     — Monitors stock, proposes orders, HITL approval
├── shift_report.py  — LLM-narrated shift summary from ERP data
└── geopol_risk.py   — Geopolitical risk digest via GDELT + LLM reasoning
```

## Tech Stack

| Layer | Tools |
|-------|-------|
| API | FastAPI, Pydantic v2, SQLAlchemy, SQLite |
| Agent | LangGraph, MemorySaver checkpointer |
| LLM | Provider-agnostic via `llm.py` (Anthropic / Gemini) |
| Testing | pytest, FastAPI TestClient, isolated test DB |

## How to Run

**Prerequisites:** Python 3.11+, pip

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Add GEMINI_API_KEY and LLM_PROVIDER=gemini to .env

# 3. Start the API
uvicorn main:app --reload

# 4. Seed the database
python seed.py

# 5. Run the ReorderAgent
python agent.py

# 6. Run reports
python shift_report.py
python geopol_risk.py
```

## Project Structure

```
├── main.py                  # App instantiation and router registration
├── models.py                # Pydantic data contracts
├── db_models.py             # SQLAlchemy ORM models
├── database.py              # Engine, session factory, Base
├── exceptions.py            # Domain exception definitions
├── llm.py                   # Swappable LLM provider abstraction
├── agent.py                 # LangGraph ReorderAgent with HITL
├── seed.py                  # Database seeding script
├── shift_report.py          # Shift/morning report script
├── geopol_risk.py           # Geopolitical risk digest script
├── repos/                   # Repository layer (data access)
├── services/                # Service layer (business logic)
├── routers/                 # Router layer (HTTP endpoints)
├── conftest.py              # pytest fixtures and test DB lifecycle
└── test_api.py              # Integration test suite
```

## Key Design Decisions

- **Separation of concerns is functional, not aesthetic** — each layer has one 
  responsibility. The repository is ignorant of HTTP. The service is ignorant 
  of HTTP. The router is ignorant of business logic.
- **LLMs at judgment boundaries only** — reorder calculation, stock comparison, 
  and status transitions are deterministic Python. LLMs generate narratives, 
  surface risks, and justify recommendations.
- **Provider isolation** — `call_llm(prompt)` is the only public interface in 
  `llm.py`. Swapping providers requires one env var change.
- **The repository layer exists to be swapped** — in-memory dicts were replaced 
  with SQLAlchemy without touching service or router layers.
```
