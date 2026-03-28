import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from models import LLMModel
from scorer import get_recommendations, PROFILES
import os
from datetime import datetime, timedelta

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

st.set_page_config(page_title="Epineon AI - LLM Monitor", page_icon="🧠", layout="wide")

st.title("🧠 Epineon AI: LLM Monitoring System")
st.markdown("Automated system for collecting, normalizing, scoring, and recommending Large Language Models based on Enterprise needs.")

# Sidebar Filters
st.sidebar.header("Configuration")
selected_profile = st.sidebar.selectbox("Select Enterprise Profile", list(PROFILES.keys()))
commercial_only = st.sidebar.checkbox("Commercial Use Only (Exclude Non-Commercial)")

db = get_db()
all_models = db.query(LLMModel).all()

if not all_models:
    st.warning("No data found! Please run the collector script first.")
    st.stop()

# Auto-generation of recommendations
st.header(f"🏆 Top Recommendations for {selected_profile}")
recs = get_recommendations(db, profile=selected_profile, commercial_only=commercial_only, top_k=5)

if recs:
    cols = st.columns(3)
    for i, rec in enumerate(recs[:3]):
        with cols[i]:
            st.metric(label=f"Rank {i+1}: {rec['model_name']}", value=f"{rec['score']}/100")
            st.caption(f"License: {rec['license']} | Intel: {rec['intelligence_score']}")
            
    # Show detailed table
    st.subheader("Comparison Table")
    df = pd.DataFrame(recs)
    df = df.rename(columns={
        "model_name": "Model", 
        "score": "Composite Score", 
        "license": "License",
        "intelligence_score": "Intelligence",
        "cost_per_1m_tokens": "Cost per 1M Tokens ($)",
        "speed_tokens_sec": "Speed (Tok/s)",
        "context_window": "Context Window"
    })
    st.dataframe(df, use_container_width=True)
else:
    st.info("No models found matching the criteria.")

# Show Newly Detected Models (last 24h)
st.divider()
st.subheader("✨ Newly Detected Models (Last 24h)")
now = datetime.utcnow()
twenty_four_hours_ago = now - timedelta(hours=24)
new_models = db.query(LLMModel).filter(LLMModel.last_updated >= twenty_four_hours_ago).all()

if new_models:
    new_df = pd.DataFrame([{"Name": m.name, "Added At": m.last_updated.strftime("%Y-%m-%d %H:%M")} for m in new_models])
    st.dataframe(new_df)
else:
    st.info("No new models detected recently.")

# Report Generation
st.divider()
st.subheader("📄 Daily Digest Report")

def generate_report():
    report = f"# Epineon AI - LLM Daily Digest ({datetime.today().strftime('%Y-%m-%d')})\n\n"
    report += "## Top Models by Profile\n\n"
    for profile in PROFILES.keys():
        profile_recs = get_recommendations(db, profile=profile, commercial_only=False, top_k=3)
        report += f"### {profile}\n"
        for i, r in enumerate(profile_recs):
            report += f"{i+1}. **{r['model_name']}** (Score: {r['score']})\n"
            report += f"   - *Cost*: ${r['cost_per_1m_tokens']} | *Intel*: {r['intelligence_score']} | *Speed*: {r['speed_tokens_sec']} tok/s\n\n"
            
    report += "## Market Movements Summary\n"
    report += "The models above have been selected dynamically based on customized profile weights balancing intelligence, cost, speed, and latency requirements specific to Enterprise deployments. "
    if new_models:
        report += f"\n\n**{len(new_models)} new models** were detected in the last 24 hours.\n"

    return report

if st.button("Generate Markdown Digest Report"):
    markdown_content = generate_report()
    st.markdown("### Preview:")
    st.markdown(markdown_content)
    
    with open("daily_digest_report.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    st.success("Report successfully saved as `daily_digest_report.md` in the repository root!")
