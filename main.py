"""
Module 2B: REST API
===================
FastAPI server exposing all endpoints for the LLM Monitoring System.
Endpoints:
  - GET /                → Welcome + available routes
  - GET /profiles        → All available enterprise profiles with descriptions
  - GET /recommend       → Top K scored models for a profile
  - GET /models          → All models with full metrics
  - GET /models/new      → Newly detected models (last 24h)
  - GET /models/movements→ Price drops, new arrivals, ranking changes
  - GET /report          → Auto-generated Markdown digest report
"""

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse
from pathlib import Path
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, LLMModel
from scorer import get_recommendations, PROFILES
from datetime import datetime, timedelta

# Initialize tables if not already present
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EPINEON AI — LLM Monitoring API",
    description="Technical Challenge Backend: Collects, scores, and recommends LLMs for Enterprise profiles. Data from Artificial Analysis, LMSYS Arena, HuggingFace, and OpenRouter.",
    version="2.0.0"
)

# Allow browser-based frontends (including index.html) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the dashboard at the root URL."""
    html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard not found. Make sure index.html is in the same folder.</h1>")


@app.get("/api")
def api_info():
    return {
        "service": "EPINEON AI — LLM Intelligence Monitor",
        "version": "2.0.0",
        "endpoints": [
            "/profiles", "/recommend", "/models",
            "/models/new", "/models/movements", "/report"
        ]
    }


@app.get("/profiles")
def list_profiles():
    """Returns all available enterprise profiles with descriptions and weights."""
    result = {}
    for name, config in PROFILES.items():
        result[name] = {
            "description": config["description"],
            "weights": {k: v for k, v in config.items() if k != "description"}
        }
    return {"profiles": list(PROFILES.keys()), "details": result}


@app.get("/recommend")
def recommend_models(
    profile: str = Query("Coding/Dev", description="Enterprise profile"),
    commercial: bool = Query(False, description="Exclude non-commercial licenses"),
    top_k: int = Query(5, description="Number of results (1-33)"),
    db: Session = Depends(get_db)
):
    """Returns the top K recommended LLMs with composite scores and justifications."""
    top_k = min(max(top_k, 1), 33)
    try:
        recommendations = get_recommendations(db, profile=profile, commercial_only=commercial, top_k=top_k)
        return {
            "profile": profile,
            "commercial_only": commercial,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/models")
def all_models(db: Session = Depends(get_db)):
    """Returns all models in the database with full metrics."""
    models = db.query(LLMModel).all()
    return {
        "total": len(models),
        "models": [
            {
                "name": m.name,
                "intelligence_score": m.intelligence_score,
                "arena_elo": m.arena_elo,
                "price_input": m.price_input_token,
                "price_output": m.price_output_token,
                "cost_per_1m": round((m.price_input_token or 0) + (m.price_output_token or 0), 2),
                "speed_tokens_sec": m.speed_tokens_per_sec,
                "ttft_latency": m.ttft_latency,
                "context_window": m.context_window,
                "license": m.license_type,
                "data_source": m.data_source,
                "first_seen": m.first_seen.isoformat() if m.first_seen else None,
                "last_updated": m.last_updated.isoformat() if m.last_updated else None,
            }
            for m in models
        ]
    }


@app.get("/models/new")
def newly_detected(
    hours: int = Query(24, description="Lookback window in hours"),
    db: Session = Depends(get_db)
):
    """Returns models first detected within the specified time window."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    new_models = db.query(LLMModel).filter(LLMModel.first_seen >= cutoff).all()
    return {
        "window_hours": hours,
        "count": len(new_models),
        "models": [
            {
                "name": m.name,
                "intelligence_score": m.intelligence_score,
                "arena_elo": m.arena_elo,
                "license": m.license_type,
                "first_seen": m.first_seen.isoformat() if m.first_seen else None,
            }
            for m in new_models
        ]
    }


@app.get("/models/movements")
def market_movements(db: Session = Depends(get_db)):
    """Returns significant market movements: price drops, new models, notable changes."""
    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
    all_models = db.query(LLMModel).all()
    
    # Price drops
    price_drops = []
    for m in all_models:
        if m.previous_price_input is not None:
            old_cost = (m.previous_price_input or 0) + (m.previous_price_output or 0)
            new_cost = (m.price_input_token or 0) + (m.price_output_token or 0)
            if new_cost < old_cost:
                pct = round(((old_cost - new_cost) / old_cost) * 100, 1) if old_cost > 0 else 0
                price_drops.append({
                    "name": m.name,
                    "old_cost": round(old_cost, 2),
                    "new_cost": round(new_cost, 2),
                    "drop_pct": pct,
                })
    
    # New arrivals
    new_arrivals = [
        {"name": m.name, "first_seen": m.first_seen.isoformat() if m.first_seen else None}
        for m in all_models if m.first_seen and m.first_seen >= cutoff_24h
    ]

    return {
        "price_drops": price_drops,
        "new_arrivals": new_arrivals,
        "total_models": len(all_models),
    }


@app.get("/report", response_class=PlainTextResponse)
def generate_report(db: Session = Depends(get_db)):
    """
    Auto-generates a Markdown digest report containing:
    - Top 5 models per profile with justifications
    - Market movements (price drops, new models)
    - Summary statistics
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=24)
    all_models = db.query(LLMModel).all()
    new_models = [m for m in all_models if m.first_seen and m.first_seen >= cutoff]
    
    r = []
    r.append(f"# 📊 EPINEON AI — Daily LLM Intelligence Digest")
    r.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}")
    r.append(f"**Models tracked:** {len(all_models)} | **New (24h):** {len(new_models)}")
    r.append(f"**Data sources:** Artificial Analysis, LMSYS Chatbot Arena, HuggingFace, OpenRouter")
    r.append("")
    r.append("---")
    r.append("")
    
    # ── TOP 5 PER PROFILE ──
    r.append("## 🏆 Top 5 Recommendations by Profile\n")
    for profile_name in PROFILES:
        desc = PROFILES[profile_name]["description"]
        recs = get_recommendations(db, profile=profile_name, commercial_only=False, top_k=5)
        r.append(f"### {profile_name}")
        r.append(f"*{desc}*\n")
        r.append("| Rank | Model | Score | Intelligence | Arena ELO | Cost/1M | Speed |")
        r.append("|------|-------|-------|-------------|-----------|---------|-------|")
        for i, rec in enumerate(recs):
            r.append(
                f"| {i+1} | **{rec['model_name']}** | {rec['score']}/100 | "
                f"{rec['intelligence_score']} | {rec['arena_elo'] or 'N/A'} | "
                f"${rec['cost_per_1m_tokens']} | {rec['speed_tokens_sec']} t/s |"
            )
        r.append("")
        # Top pick justification
        if recs:
            r.append(f"> **Top pick:** {recs[0]['model_name']} — {recs[0]['justification']}\n")
    
    r.append("---\n")
    
    # ── MARKET MOVEMENTS ──
    r.append("## 📈 Market Movements\n")
    
    # Price drops
    price_drops = []
    for m in all_models:
        if m.previous_price_input is not None:
            old_cost = (m.previous_price_input or 0) + (m.previous_price_output or 0)
            new_cost = (m.price_input_token or 0) + (m.price_output_token or 0)
            if new_cost < old_cost:
                pct = round(((old_cost - new_cost) / old_cost) * 100, 1) if old_cost > 0 else 0
                price_drops.append((m.name, old_cost, new_cost, pct))
    
    if price_drops:
        r.append("### 💸 Price Drops Detected\n")
        r.append("| Model | Old Cost | New Cost | Change |")
        r.append("|-------|----------|----------|--------|")
        for name, old, new, pct in price_drops:
            r.append(f"| {name} | ${old:.2f} | ${new:.2f} | **-{pct}%** 📉 |")
        r.append("")
    else:
        r.append("*No significant price drops detected in the last cycle.*\n")
    
    # New arrivals
    if new_models:
        r.append("### ✨ Newly Detected Models\n")
        for m in new_models:
            elo_str = f" | Arena ELO: {m.arena_elo}" if m.arena_elo else ""
            r.append(f"- **{m.name}** — Intelligence: {m.intelligence_score}{elo_str} | License: {m.license_type}")
        r.append("")
    else:
        r.append("*No new models detected in the last 24 hours.*\n")
    
    r.append("---\n")
    
    # ── SUMMARY ──
    r.append("## 📊 Summary Statistics\n")
    
    elos = [m.arena_elo for m in all_models if m.arena_elo]
    costs = [(m.price_input_token or 0) + (m.price_output_token or 0) for m in all_models]
    speeds = [m.speed_tokens_per_sec for m in all_models if m.speed_tokens_per_sec]
    intels = [m.intelligence_score for m in all_models if m.intelligence_score]
    
    r.append(f"| Metric | Min | Max | Average |")
    r.append(f"|--------|-----|-----|---------|")
    if intels:
        r.append(f"| Intelligence | {min(intels)} | {max(intels)} | {sum(intels)/len(intels):.1f} |")
    if elos:
        r.append(f"| Arena ELO | {min(elos)} | {max(elos)} | {sum(elos)/len(elos):.0f} |")
    if costs:
        r.append(f"| Cost/1M tokens | ${min(costs):.2f} | ${max(costs):.2f} | ${sum(costs)/len(costs):.2f} |")
    if speeds:
        r.append(f"| Speed (tok/s) | {min(speeds)} | {max(speeds)} | {sum(speeds)/len(speeds):.0f} |")
    
    r.append("")
    
    # License distribution
    license_counts = {}
    for m in all_models:
        lt = m.license_type or "Unknown"
        license_counts[lt] = license_counts.get(lt, 0) + 1
    
    r.append("### License Distribution\n")
    for lic, count in sorted(license_counts.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * count
        r.append(f"- **{lic}**: {count} models {bar}")
    
    r.append("\n---\n")
    r.append("*This report was auto-generated by the EPINEON AI LLM Monitoring System.*")
    r.append("*Data compiled from Artificial Analysis, LMSYS Chatbot Arena, HuggingFace Open LLM Leaderboard, and OpenRouter.*")
    
    return "\n".join(r)
