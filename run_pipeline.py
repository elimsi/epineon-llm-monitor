import schedule
import time
from collector import fetch_and_store_data
import os

def automated_pipeline():
    print("[Pipeline] Running scheduled data collection...")
    fetch_and_store_data()
    print("[Pipeline] Data collection complete. Simulating Auto-Digest generation...")
    # Normally we would call a function here to write the markdown and email/slack it.
    os.system("echo Auto-generated report tick >> crontab.log")

if __name__ == "__main__":
    print("Starting EPINEON LLM Monitor Background Scheduler...")
    # Bonus Module: Automated Monitoring Agent
    # Schedule the pipeline to run every 24 hours.
    schedule.every(24).hours.do(automated_pipeline)
    
    # Run once immediately on start
    automated_pipeline()
    
    while True:
        schedule.run_pending()
        time.sleep(60)
