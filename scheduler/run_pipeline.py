import asyncio
import logging
import os
import json
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from engine.database import SessionLocal
from engine.scorer import get_recommendations, PROFILES
from engine.models import LLMModel
from engine.collector import fetch_and_store_data

# Global log buffer for UI streaming
PIPELINE_LOGS = []

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler.pipeline")

class TerminalLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        PIPELINE_LOGS.append(msg)
        if len(PIPELINE_LOGS) > 100: PIPELINE_LOGS.pop(0)

# Attach custom handler to the root logger or specific loggers
handler = TerminalLogHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger("\u26a1 EPINEON").addHandler(handler)
logging.getLogger("scheduler.pipeline").addHandler(handler)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

os.makedirs(REPORTS_DIR, exist_ok=True)

async def run_pipeline():
    logger.info("\u26a1 Pipeline execution started...")
    try:
        # 1. Run Data Collection
        await fetch_and_store_data()
        
        # 2. Generate Report
        db = SessionLocal()
        report = generate_markdown_report(db)
        
        report_filename = f"digest_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
        report_path = os.path.join(REPORTS_DIR, report_filename)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        # 3. Update Status
        status = {
            "last_run": datetime.now().isoformat(),
            "last_report": report_filename,
            "status": "success"
        }
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f)
            
        logger.info(f"\u2705 Pipeline finished. Report saved to {report_filename}")
        db.close()
    except Exception as e:
        logger.error(f"\u274c Pipeline error: {e}")

def generate_markdown_report(db):
    report = f"# EPINEON AI \u2014 Market Digest ({datetime.today().strftime('%Y-%m-%d')})\n\n"
    report += "## Top 3 Compromise Recommendations by Profile (VIKOR Math)\n\n"
    for profile in PROFILES.keys():
        recs = get_recommendations(db, profile=profile, top_k=3)
        report += f"### {profile}\n"
        for i, r in enumerate(recs):
            report += f"{i+1}. **{r['model_name']}** (Score: {r['score']})\n"
            report += f"   - Logic: {r['justification']}\n"
    return report

scheduler = AsyncIOScheduler()

async def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(run_pipeline, 'interval', hours=24, id='daily_pipeline')
        scheduler.start()
        logger.info("APScheduler initialized.")

async def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()

async def run_now():
    asyncio.create_task(run_pipeline())

def get_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {"status": "never_run"}
