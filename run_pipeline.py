"""
Bonus Module: Automated Monitoring Agent
=========================================
APScheduler-based pipeline that runs automatically every 24 hours:
  1. Collects & updates LLM data (collector.py)
  2. Scores all profiles and generates recommendations (scorer.py)
  3. Saves a timestamped Markdown digest report to /reports/
  4. Optionally sends the digest via email (configure below)

Run standalone:  python run_pipeline.py
API status:      GET /scheduler/status
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# ─── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("epineon.scheduler")

# ─── Config ──────────────────────────────────────────────────
REPORTS_DIR   = Path(__file__).parent / "reports"
STATUS_FILE   = Path(__file__).parent / "scheduler_status.json"
RUN_INTERVAL_HOURS = 24          # change to 1 for testing

# Optional email config — set env vars or fill in here
EMAIL_ENABLED  = os.getenv("EPINEON_EMAIL_ENABLED", "false").lower() == "true"
EMAIL_FROM     = os.getenv("EPINEON_EMAIL_FROM", "")
EMAIL_TO       = os.getenv("EPINEON_EMAIL_TO", "")
EMAIL_PASSWORD = os.getenv("EPINEON_EMAIL_PASS", "")
EMAIL_SMTP     = os.getenv("EPINEON_SMTP", "smtp.gmail.com")
EMAIL_PORT     = int(os.getenv("EPINEON_SMTP_PORT", "587"))

# ─── Global status ───────────────────────────────────────────
_status = {
    "running":       False,
    "last_run":      None,
    "next_run":      None,
    "last_status":   "never_run",
    "reports":       [],
    "total_runs":    0,
    "errors":        [],
}


def save_status():
    STATUS_FILE.write_text(json.dumps(_status, indent=2, default=str))


def load_status():
    global _status
    if STATUS_FILE.exists():
        try:
            _status = json.loads(STATUS_FILE.read_text())
        except Exception:
            pass


def run_pipeline():
    """Main pipeline: collect → score → report → notify."""
    global _status
    now = datetime.now(timezone.utc)
    log.info("=" * 55)
    log.info("  EPINEON AI — Automated Pipeline starting...")
    log.info("=" * 55)

    _status["running"]    = True
    _status["last_run"]   = now.isoformat()
    _status["last_status"] = "running"
    save_status()

    try:
        # ── Step 1: Collect data ─────────────────────────────
        log.info("[1/3] Running data collector...")
        from collector import fetch_and_store_data
        fetch_and_store_data()
        log.info("      Data collection complete.")

        # ── Step 2: Generate report via API ──────────────────
        log.info("[2/3] Generating digest report...")
        report_md = _build_report()

        # ── Step 3: Save report ───────────────────────────────
        log.info("[3/3] Saving report to disk...")
        REPORTS_DIR.mkdir(exist_ok=True)
        ts         = now.strftime("%Y-%m-%d_%H-%M")
        filename   = REPORTS_DIR / f"digest_{ts}.md"
        filename.write_text(report_md, encoding="utf-8")

        # Keep track of last 10 reports
        report_entry = {
            "filename":  filename.name,
            "path":      str(filename),
            "generated": now.isoformat(),
            "size_kb":   round(filename.stat().st_size / 1024, 1),
        }
        _status["reports"].insert(0, report_entry)
        _status["reports"] = _status["reports"][:10]
        _status["total_runs"] += 1
        _status["last_status"] = "success"
        log.info(f"      Report saved: {filename.name} ({report_entry['size_kb']} KB)")

        # ── Step 4: Email (optional) ──────────────────────────
        if EMAIL_ENABLED:
            _send_email(report_md, ts)

        log.info("=" * 55)
        log.info("  Pipeline complete. Next run in %dh.", RUN_INTERVAL_HOURS)
        log.info("=" * 55)

    except Exception as e:
        _status["last_status"] = f"error: {e}"
        _status["errors"].insert(0, {"time": now.isoformat(), "msg": str(e)})
        _status["errors"] = _status["errors"][:5]
        log.error("Pipeline failed: %s", e, exc_info=True)

    finally:
        _status["running"] = False
        save_status()


def _build_report() -> str:
    """Generate report directly using scorer (no HTTP call needed)."""
    from database import SessionLocal
    from scorer import get_recommendations, PROFILES
    from models import LLMModel
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    db  = SessionLocal()
    try:
        all_models  = db.query(LLMModel).all()
        cutoff      = now - timedelta(hours=24)
        new_models  = [m for m in all_models if m.first_seen and
                       m.first_seen.replace(tzinfo=timezone.utc) >= cutoff]

        r = []
        r.append(f"# EPINEON AI — Daily LLM Intelligence Digest")
        r.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}")
        r.append(f"**Models tracked:** {len(all_models)} | **New (24h):** {len(new_models)}")
        r.append(f"**Author:** EL KHOBZI Ismail | ESITH Challenge 2026")
        r.append(f"**Data sources:** Artificial Analysis · LMSYS Arena · HuggingFace · OpenRouter")
        r.append("\n---\n")

        r.append("## Top 5 Recommendations by Profile\n")
        for profile_name in PROFILES:
            recs = get_recommendations(db, profile=profile_name, top_k=5)
            r.append(f"### {profile_name}")
            r.append(f"*{PROFILES[profile_name]['description']}*\n")
            r.append("| Rank | Model | Score | Intel | ELO | Cost/1M | Speed |")
            r.append("|------|-------|-------|-------|-----|---------|-------|")
            for i, rec in enumerate(recs):
                r.append(f"| {i+1} | **{rec['model_name']}** | {rec['score']} | "
                         f"{rec['intelligence_score']} | {rec['arena_elo'] or 'N/A'} | "
                         f"${rec['cost_per_1m_tokens']} | {rec['speed_tokens_sec']} t/s |")
            r.append("")
            if recs:
                r.append(f"> **Top pick:** {recs[0]['model_name']} — {recs[0]['justification']}\n")

        r.append("---\n")
        r.append("## Market Movements\n")
        price_drops = []
        for m in all_models:
            if m.previous_price_input is not None:
                old = (m.previous_price_input or 0) + (m.previous_price_output or 0)
                new = (m.price_input_token or 0) + (m.price_output_token or 0)
                if new < old:
                    pct = round(((old - new) / old) * 100, 1) if old > 0 else 0
                    price_drops.append((m.name, old, new, pct))

        if price_drops:
            r.append("### Price Drops\n")
            r.append("| Model | Old | New | Drop |")
            r.append("|-------|-----|-----|------|")
            for name, old, new, pct in price_drops:
                r.append(f"| {name} | ${old:.2f} | ${new:.2f} | **-{pct}%** |")
            r.append("")
        else:
            r.append("*No price drops detected.*\n")

        if new_models:
            r.append("### New Models Detected\n")
            for m in new_models:
                r.append(f"- **{m.name}** — Intel: {m.intelligence_score} | ELO: {m.arena_elo}")
            r.append("")

        r.append("---\n")
        r.append(f"*Auto-generated by EPINEON AI Monitoring Agent · {now.strftime('%Y-%m-%d')}*")
        return "\n".join(r)
    finally:
        db.close()


def _send_email(report_md: str, ts: str):
    """Send digest report via email using SMTP."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    try:
        msg = MIMEMultipart()
        msg["From"]    = EMAIL_FROM
        msg["To"]      = EMAIL_TO
        msg["Subject"] = f"[EPINEON AI] Daily LLM Digest — {ts}"

        body = f"Your daily LLM intelligence digest is attached.\n\n" \
               f"Generated at {ts} UTC by EPINEON AI Monitoring Agent.\n" \
               f"Author: EL KHOBZI Ismail"
        msg.attach(MIMEText(body, "plain"))

        # Attach the .md file
        part = MIMEBase("application", "octet-stream")
        part.set_payload(report_md.encode("utf-8"))
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=digest_{ts}.md")
        msg.attach(part)

        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        log.info("      Email sent to %s", EMAIL_TO)
    except Exception as e:
        log.error("Email failed: %s", e)


def get_status() -> dict:
    """Return current scheduler status (called by the API)."""
    return _status


# ─── Scheduler setup ─────────────────────────────────────────

scheduler = BackgroundScheduler(timezone="UTC")

def start_scheduler():
    load_status()
    scheduler.add_job(
        func=run_pipeline,
        trigger=IntervalTrigger(hours=RUN_INTERVAL_HOURS),
        id="pipeline",
        name="EPINEON Pipeline",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    # Update next_run
    job = scheduler.get_job("pipeline")
    if job and job.next_run_time:
        _status["next_run"] = job.next_run_time.isoformat()
        save_status()
    log.info("Scheduler started — runs every %dh | Next: %s",
             RUN_INTERVAL_HOURS, _status.get("next_run", "unknown"))


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("Scheduler stopped.")


# ─── Standalone execution ─────────────────────────────────────

if __name__ == "__main__":
    import time
    log.info("Starting EPINEON AI Automated Pipeline (standalone mode)")
    log.info("Running immediately, then every %dh...", RUN_INTERVAL_HOURS)
    run_pipeline()   # run once immediately
    start_scheduler()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
