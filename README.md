# ⚡ EPINEON AI: Elite LLM Intelligence Control Center

> **ESITH Technical Challenge 2026** — *Ultimate Version*
> Designed by EL KHOBZI Ismail

EPINEON AI is an enterprise-grade ecosystem developed to autonomously collect, score, and recommend Large Language Models (LLMs) for commercial deployment. It goes beyond simple leaderboards by implementing advanced mathematical modeling (Shannon Entropy + VIKOR) to provide objective, data-driven model recommendations based on specific enterprise use cases.

---

## 🏗️ System Architecture

The project has been refactored into a modular, production-ready architecture:

```text
epineon-llm-monitor/
├── api/
│   ├── index.html       # The Elite Frontend UI (Glassmorphism, 3D Canvas, Radar)
│   └── main.py          # FastAPI Backend Routes
├── engine/
│   ├── collector.py     # Async Data Pipeline (OpenRouter + Curated baseline)
│   ├── database.py      # SQLite / SQLAlchemy ORM Initialization
│   ├── models.py        # Database Schemas
│   └── scorer.py        # VIKOR & Shannon Entropy Math Engine
├── scheduler/
│   └── run_pipeline.py  # APScheduler for daily continuous monitoring
├── run.py               # Main Entry Point (Uvicorn Server)
└── requirements.txt     # Python Dependencies
```

---

## 🧠 Core Engineering Features

### 1. Dynamic Asynchronous Data Sync
Unlike static JSON files, EPINEON implements an asynchronous, multi-threaded worker pipeline using `HTTPX` and `asyncio`. 
- **Curated Baseline**: Ensures stable data for leading models (GPT-4o, Claude 3.5 Sonnet, Claude 3 & 4.6 Opus, Gemini, etc.).
- **Live OpenRouter Sync**: Real-time fetching and ingestion of over 300+ commercial models alongside exact token pricing metrics dynamically inserted into the SQLite database.

### 2. Shannon Entropy & VIKOR Math Engine
We do not rely on basic score averaging. The `scorer.py` engine computes recommendations via:
- **Shannon Entropy Weighting**: Autonomously determines the statistical weight of each criterion (Intelligence, Speed, Latency, Cost) based on the current dataset's variance. 
- **VIKOR Compromise Scoring**: Ranks models by measuring their proximity to the "Ideal Solution" while minimizing "Regret" (the distance to the worst metric).
- **Enterprise Profiles**: Combines Entropy objective weights with subjective multiplier profiles (`Coding/Dev`, `Reasoning/Analysis`, `Minimum Cost`, `Enterprise Agents`, `Balanced`).

### 3. Elite Graphical Interface
Served directly via the API, the frontend boasts top-tier UX/UI design:
- **Real-Time Cost Calculator**: Move sliders to calculate estimated monthly costs based on token throughput, seamlessly adapting per model.
- **3D Interactive Podium**: Built with `Three.js`, visualizes the top 10 ranked LLMs in an interactive, rotatable cyber-arena.
- **Multi-Criteria Radar**: Implements strict `min-max normalization` (0-100 scales) natively inside the backend to draw perfect capability geometry across all 6 dimensions.
- **Live Terminal HUD**: Intercepts backend pipeline signals to simulate engine activity on the screen.

---

## 🚀 How to Run the Project

Follow these exact steps to deploy the Elite version of EPINEON AI locally:

### Step 1: Install Dependencies
Ensure you have `Python 3.10+` installed on your machine.
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Core Data (Optional but Recommended)
Before starting the server, spawn the async workers to fetch the latest state of the LLM Market and sync the Claude Opus models.
```bash
python -m engine.collector
```
*(You should see an output indicating over 300 models have been saved into the database)*

### Step 3: Start the Control Center
To launch the FastAPI server and the integrated Frontend at the same time, execute:
```bash
python run.py
```

### Step 4: Access the Dashboard
Once the server boots up, open your browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

*(Note: The `index.html` frontend is automatically served by FastAPI on the root `/` path. You do not need to open the html file manually!)*

---

## 🔌 API Endpoints Reference

| Route | Method | Description |
|-------|--------|-------------|
| `/` | `GET` | Serves the immersive `index.html` frontend. |
| `/profiles` | `GET` | Returns the available Enterprise Weight Profiles. |
| `/recommend` | `GET` | Computes the VIKOR rank and returns normalized bounds. |
| `/scheduler/run` | `POST` | Manually triggers the OpenRouter Async pipeline. |
| `/report` | `GET` | Generates a Markdown digest summarizing market leaders. |
| `/ws/pipeline` | `WS` | WebSocket endpoint streaming engine activity logs. |
