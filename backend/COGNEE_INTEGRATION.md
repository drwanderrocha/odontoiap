# Cognee Integration for OdontoAI — Quick Start

## Overview
Cognee provides persistent long-term memory for AI agents. For OdontoAI, it stores:
- **Biomechanical rules** (M/F ratios, attachment designs, overcorrection) — from the teach workspace
- **Clinical cases** (anonymized) — for learning from outcomes
- **Literature summaries** — RAG-ready for clinical questions
- **User preferences** — teaching style, notation, clinical protocols

---

## 1. Installation

```bash
cd /opt/data/home/dentista-agente-prototipo/backend

# Install dependencies
uv pip install -r requirements.txt
# or: pip install -r requirements.txt
```

---

## 2. Configuration

### Local Mode (default — embedded SQLite/LanceDB/KuzuDB)
```bash
# Just need an LLM API key (OpenRouter free tier works)
export LLM_API_KEY="sk-or-v1-..."  # OpenRouter key
```

### Local with Postgres (recommended for production)
```bash
export LLM_API_KEY="sk-or-v1-..."
export DATABASE_URL="postgresql://cognee:cognee@localhost:5432/cognee_db"
# Cognee will auto-use Postgres for graph + vectors + cache
```

### Cloud Mode (Cognee Cloud)
```bash
export LLM_API_KEY="sk-or-v1-..."
export COGNEE_BASE_URL="https://your-instance.cognee.ai"
export COGNEE_API_KEY="ck_..."
```

---

## 3. Initialize Database (if using Postgres)

```bash
# Start Postgres with pgvector
docker run -d \
  --name cognee-postgres \
  -e POSTGRES_USER=cognee \
  -e POSTGRES_PASSWORD=cognee \
  -e POSTGRES_DB=cognee_db \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Wait a few seconds, then run migrations (Cognee does this auto)
```

---

## 4. Populate Biomechanical Knowledge

```bash
# From backend directory
cd /opt/data/home/dentista-agente-prototipo/backend
python populate_memory.py
```

This loads 10 biomechanical rules from Lição 01 (M/F ratios, attachment designs, overcorrection factors).

---

## 5. Usage in OdontoAI Backend

### In your FastAPI app (`main.py`):

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from memory_cognee import get_memory, close_memory

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    mem = await get_memory()
    yield
    # Shutdown
    await close_memory()

app = FastAPI(lifespan=lifespan)

@app.post("/clinical/plan")
async def create_plan(case: ClinicalCase):
    mem = await get_memory()
    
    # Retrieve relevant biomechanical rules
    rules = await mem.get_biomechanical_rules(
        movement_type=case.movement,
        tooth_type=case.tooth
    )
    
    # Retrieve similar cases
    similar = await mem.find_similar_cases(
        diagnosis=case.diagnosis,
        movement_types=[case.movement]
    )
    
    # Build prompt with context for LLM
    ...
```

### Direct memory operations:

```python
mem = await get_memory()

# Store a new clinical case outcome
await mem.store_clinical_case(
    case_id="case_2024_001",
    diagnosis="Class II div 1, deep bite",
    treatment_plan={"aligners": 24, "elastics": "Class II", "IPR": "5-5 sup/inf"},
    biomechanics_notes="Used power ridges on 11/21 for torque, optimized rotation attachments on 13/23",
    outcome="Excellent torque control, rotation 90% predicted"
)

# Search literature
papers = await mem.search_literature(
    "intrusion mechanics clear aligners attachments",
    tags=["intrusion", "attachments"]
)

# Store user preference
await mem.store_user_preference(
    user_id="dr_wander",
    preference_key="notation_system",
    preference_value="FDI with biomechanical annotations",
    context="Prefers M/F ratio in mm, overcorrection as multiplier"
)
```

---

## 6. Architecture Integration

```
┌─────────────────────────────────────────────────────────────┐
│                        OdontoAI Voice Agent                  │
│  (faster-whisper → LLM → edge-tts → WebSocket)              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8080)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Clinical   │  │  Biomech    │  │  Literature RAG     │  │
│  │  Planner    │──│  Engine     │──│  (Cognee recall)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                   │               │
│         ▼                ▼                   ▼               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Cognee Memory Layer                     │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │    │
│  │  │  Graph   │  │  Vector  │  │  Cache   │           │    │
│  │  │ (Kuzu/   │  │ (LanceDB/│  │ (SQLite/ │           │    │
│  │  │  Neo4j)  │  │ pgvector)│  │  Redis)  │           │    │
│  │  └──────────┘  └──────────┘  └──────────┘           │    │
│  │         ▲                ▲                ▲           │    │
│  │  remember()         recall()        forget()          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Key API Methods

| Method | Purpose |
|--------|---------|
| `store_biomechanical_rule()` | Save M/F ratio, attachment design, overcorrection |
| `get_biomechanical_rules(movement, tooth)` | Retrieve rules for planning |
| `store_clinical_case()` | Save anonymized case outcome |
| `find_similar_cases(diagnosis, movements)` | Case-based reasoning |
| `store_literature_summary()` | Index papers for RAG |
| `search_literature(query, tags)` | Semantic search papers |
| `store_user_preference()` | Personalize teaching/clinical style |
| `store_session_context(session_id, ...)` | Fast transient memory |
| `forget_dataset()` | Nuclear option — wipe all |

---

## 8. Testing Retrieval

```python
# Quick test
import asyncio
from memory_cognee import ClinicalMemory, MemoryConfig

async def test():
    mem = ClinicalMemory(MemoryConfig(llm_api_key="sk-or-..."))
    await mem.initialize()
    
    rules = await mem.get_biomechanical_rules("bodily_translation")
    print(f"Found {len(rules)} rules")
    for r in rules:
        print(f"  {r['metadata']}")
    
    await mem.close()

asyncio.run(test())
```

---

## 9. Next Steps

1. **Populate literature** — Add key papers (Nanda & Tosun, Simon 2018, Kwon 2020, Gong 2022, Rossini 2015)
2. **Attach to teach workspace** — Auto-sync `learning-records/*.md` → Cognee on each session
3. **Clinical copilot prompt** — Build system prompt that injects biomechanical rules + similar cases
4. **Voice integration** — "Carlos, qual o M/F ideal para torque vestibular no 11?" → recall → respond
5. **Outcome tracking** — Store case results → improve overcorrection factors via feedback loop

---

## 10. Resources

- **Cognee Docs**: https://docs.cognee.ai/
- **Research Paper**: [Optimizing Knowledge Graphs for LLM Reasoning](https://arxiv.org/abs/2505.24478)
- **Discord**: https://discord.gg/NQPKmU5CCg
- **OdontoAI Teach Workspace**: `/opt/data/skills/teach/` (Lição 01 = biomechanical rules source)