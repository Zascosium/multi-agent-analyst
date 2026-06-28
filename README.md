# Multi-Agent Data Analyst

Upload a CSV. A crew of LLM agents collaborates to produce a comprehensive data analysis report — complete with statistics, charts, and written recommendations.

> **Live demo:** *(link after deploy)*

---

## Architecture

```
User (CSV + question)
        │
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │              LangGraph Supervisor (Orchestrator)         │
  │   Creates an analysis plan; routes between agents        │
  └──────┬─────────────────┬──────────────────┬────────────┘
         │                 │                  │
         ▼                 ▼                  ▼
  ┌─────────────┐  ┌──────────────────┐  ┌──────────────┐
  │   Analyst   │  │   Visualizer     │  │    Writer    │
  │             │  │                  │  │              │
  │ Writes &    │  │ Writes & runs    │  │ Synthesizes  │
  │ runs pandas │  │ matplotlib code  │  │ findings →   │
  │ code in E2B │  │ in E2B sandbox   │  │ Markdown     │
  │ sandbox     │  │ → base64 charts  │  │ report       │
  │ Self-heals  │  │                  │  │              │
  │ on errors   │  └──────────────────┘  └──────────────┘
  └─────────────┘
         │
    SSE stream → FastAPI → Svelte UI
```

### Key design decisions

| Decision | Rationale |
|---|---|
| **LangGraph** over ad-hoc LangChain | Explicit state machine: nodes + edges, debuggable, resumable |
| **E2B sandbox** for code execution | LLM-generated code runs isolated; no host risk |
| **Self-healing analyst** | stderr fed back into LLM for up to 3 retry iterations |
| **SSE streaming** | Users see agents working in real time — compelling demo |
| **Fargate + Terraform** | Serverless containers, zero infra management, IaC |

---

## Stack

- **Orchestration:** LangGraph + LangChain
- **LLM:** Claude Sonnet (Anthropic)
- **Sandbox:** E2B Code Interpreter
- **Backend:** FastAPI + Server-Sent Events
- **Frontend:** SvelteKit
- **Infra:** AWS ECS Fargate + ECR via Terraform
- **CI/CD:** GitHub Actions

---

## Quick start (local)

```bash
# 1. Clone & configure
git clone <repo-url>
cd multi-agent-analyst
cp .env.example .env
# Fill in ANTHROPIC_API_KEY and E2B_API_KEY in .env

# 2. Run everything
docker-compose up

# API:      http://localhost:8000/docs
# Frontend: http://localhost:5173
```

### Without Docker

```bash
pip install -e ".[dev]"
uvicorn api.main:app --reload          # backend

cd frontend && npm install && npm run dev  # frontend (separate terminal)
```

---

## Run tests

```bash
pytest --cov=. --cov-report=term-missing
```

---

## Deploy to AWS

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Fill in your values

terraform init
terraform plan
terraform apply

# Push image to ECR (see GitHub Actions workflow for full CI/CD)
```

---

## Project structure

```
multi-agent-analyst/
├── agents/
│   ├── graph.py          # LangGraph StateGraph — the orchestration core
│   ├── analyst.py        # Code-gen + self-healing execution agent
│   ├── visualizer.py     # Chart-generation agent
│   └── writer.py         # Report synthesis agent
├── core/
│   ├── sandbox.py        # E2B session lifecycle + code runner
│   ├── prompts.py        # System prompts for each agent role
│   ├── schemas.py        # AnalysisState TypedDict + Pydantic models
│   └── config.py         # Settings (pydantic-settings)
├── api/
│   ├── main.py           # FastAPI app + CORS
│   ├── jobs.py           # In-process job store + SSE queue
│   └── routes/
│       ├── analysis.py   # POST /analyze, GET /stream/{id}, GET /report/{id}
│       └── health.py
├── frontend/             # SvelteKit app
├── infra/terraform/      # ECS Fargate + ECR + ALB + SSM secrets
├── tests/
└── .github/workflows/ci.yml
```

---

## How the self-healing loop works

The Analyst agent uses a retry loop (up to `MAX_RETRIES=3`):

1. LLM generates pandas code from the dataset schema + analysis plan
2. Code executes in an E2B sandbox
3. On failure, `stderr` + the broken code are fed back to the LLM with a fix prompt
4. Repeat until success or max retries

This pattern — **LLM → execute → observe error → LLM again** — is the foundation of autonomous coding agents.
