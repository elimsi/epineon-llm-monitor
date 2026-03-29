import asyncio
import logging
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime

from engine.database import get_db, engine, init_db
from engine.models import LLMModel
from engine.scorer import get_recommendations, PROFILES
from scheduler.run_pipeline import start_scheduler, stop_scheduler, PIPELINE_LOGS, run_now

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.main")

app = FastAPI(title="EPINEON AI \u2014 LLM Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()
    
    # Auto-fetch if DB is essentially empty (perfect for cloud deployment)
    try:
        db = next(get_db())
        if not db.query(LLMModel).first():
            from engine.collector import fetch_and_store_data
            asyncio.create_task(fetch_and_store_data())
    finally:
        db.close()
        
    await start_scheduler()
    logger.info("EPINEON API Started. Scheduler active.")

@app.on_event("shutdown")
async def shutdown_event():
    await stop_scheduler()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    import os
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/profiles")
async def get_profiles():
    return {"profiles": list(PROFILES.keys())}

@app.get("/recommend")
async def recommend(
    profile: str = "Balanced", 
    prompt_tokens: int = 1000, 
    completion_tokens: int = 1000,
    top_k: int = 10,
    db: Session = Depends(get_db)
):
    recs = get_recommendations(db, profile, prompt_tokens, completion_tokens, top_k)
    return {"recommendations": recs}

@app.get("/models")
async def list_models(db: Session = Depends(get_db)):
    models = db.query(LLMModel).all()
    return {"total": len(models), "models": models}

@app.post("/scheduler/run")
async def trigger_pipeline():
    await run_now()
    return {"message": "Pipeline execution triggered manually."}

@app.websocket("/ws/pipeline")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established for pipeline logs.")
    try:
        # Send existing logs
        for log in PIPELINE_LOGS:
            await websocket.send_text(log)
            
        last_log_idx = len(PIPELINE_LOGS)
        while True:
            if len(PIPELINE_LOGS) > last_log_idx:
                for i in range(last_log_idx, len(PIPELINE_LOGS)):
                    await websocket.send_text(PIPELINE_LOGS[i])
                last_log_idx = len(PIPELINE_LOGS)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
