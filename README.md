# EPINEON AI: LLM Monitoring System

## Overview
This repository contains the backend, scoring engine, and visualization dashboard for the Epineon AI Technical Challenge (PFE 2026). It automatically collects LLM benchmark data and dynamically scores them based on configurable Enterprise Profiles.

## Architecture

**Module 1: Data Collection & Normalization**
- Implemented via `collector.py` using Python's requests and SQLAlchemy.
- Data from over 20+ distinct models is collected, cleaned, normalized, and stored in a lightweight zero-config SQLite backend (`llm_monitoring.db`).

**Module 2: Recommendation Engine & API**
- Implemented in `scorer.py`. The formula calculates a composite rank based on Enterprise Profile dynamic weights (e.g., Coding places Intelligence over Cost, Minimum Cost places Cost over Intelligence).
- A RESTful architecture exposed using **FastAPI** (`main.py`) which processes thousands of dynamic requests natively.

**Module 3: Visual Dashboard & Digest**
- Implemented using **Streamlit** (`dashboard.py`).
- Allows visual profile filtering and dynamically auto-generates a Markdown analysis digest containing the latest Market insights.

**Bonus Module: Automated Agent**
- Included `run_pipeline.py` utilizing a Python Scheduler to refresh the pipeline programmatically in the background every 24 hours.

## Local Setup

**Requirements:**
- Python 3.10+
- `pip install -r requirements.txt`

**Execution Steps:**
1. **Initialize DB & Collect Data:**
   `python collector.py`
2. **Start the API Server (Module 2):**
   `uvicorn main:app --reload`
3. **Start the Dynamic Dashboard (Module 3):**
   `streamlit run dashboard.py`
4. **(Optional) Run Background Pipeline:**
   `python run_pipeline.py`

## Technologies Used
- **Backend:** Python, SQLAlchemy, SQLite
- **API framework:** FastAPI, Uvicorn
- **UI & Visualization:** Streamlit, Pandas
- **Version Control:** Git (Trunk-based branch strategy)
