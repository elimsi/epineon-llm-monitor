# EPINEON AI: LLM Intelligence Monitoring System

> **ESITH Technical Challenge 2026** — Automated system for collecting, scoring, and recommending Large Language Models for Enterprise deployment.

## Architecture

```
┌────────────────────┐     ┌──────────────────┐     ┌────────────────────────┐
│  Module 1          │     │  Module 2        │     │  Module 3              │
│  Data Collection   │────>│  Scoring Engine  │────>│  Dashboard + Reports   │
│  collector.py      │     │  scorer.py       │     │  index.html            │
│                    │     │  main.py (API)   │     │  (Auto-generated .md)  │
└────────────────────┘     └──────────────────┘     └────────────────────────┘
        │                          │                          │
   33 models from:          6-dimension scoring         7 visualization types
   - Artificial Analysis    - Intelligence               - 3D Podium
   - LMSYS Chatbot Arena    - Arena ELO                  - Bar Charts
   - HuggingFace            - Cost (lower=better)        - Radar Charts
   - OpenRouter             - Speed                      - Bubble Scatter
                            - Latency (lower=better)     - ELO Rankings
                            - Context Window             - Model Comparison
                                                         - Digest Reports
```

## Features

- **33 real LLM models** with data from 4 authoritative sources
- **6-dimension weighted scoring** with Arena ELO integration
- **5 Enterprise Profiles**: Coding/Dev, Reasoning/Analysis, Minimum Cost, Enterprise Agents, Balanced
- **Auto-generated justifications** explaining why each model was recommended
- **Price change tracking** for detecting market movements
- **7 REST API endpoints** via FastAPI
- **Professional dashboard** with 3D effects, glassmorphism, and 6 chart types
- **Auto-generated Markdown digest reports** with recommendations per profile
- **Background scheduler** for automated 24h data refresh

## Quick Start

**Requirements:** Python 3.10+

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed the database (33 models)
python collector.py

# 3. Start the API server
python -m uvicorn main:app --reload

# 4. Open the dashboard
# Double-click index.html in your browser
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Service info and available routes |
| `GET /profiles` | Enterprise profiles with descriptions and weights |
| `GET /recommend?profile=Coding/Dev&top_k=5` | Top K scored models with justifications |
| `GET /models` | All models with full metrics |
| `GET /models/new?hours=24` | Newly detected models |
| `GET /models/movements` | Price drops and market changes |
| `GET /report` | Auto-generated Markdown digest report |

## Technology Stack

- **Backend:** Python 3, SQLAlchemy, SQLite
- **API:** FastAPI, Uvicorn, CORS-enabled
- **Frontend:** HTML5, CSS3 (Glassmorphism), Chart.js
- **Data Sources:** Artificial Analysis, LMSYS Arena, HuggingFace, OpenRouter
- **Scheduling:** Python `schedule` library
- **Version Control:** Git
