from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base
from scorer import get_recommendations, PROFILES

# Initialize tables if not already present
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LLM Monitoring API",
    description="EPINEON AI Technical Challenge Backend - Recommends LLMs based on Enterprise profiles.",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Welcome to the LLM Monitoring System. Available endpoints: /recommend, /profiles"}

@app.get("/profiles")
def list_profiles():
    """Returns all available enterprise profiles and their metric weights."""
    return {"profiles": list(PROFILES.keys())}

@app.get("/recommend")
def recommend_models(
    profile: str = Query("Coding/Dev", description="The use-case profile. Valid options: " + ", ".join(PROFILES.keys())),
    commercial: bool = Query(False, description="Exclude non-commercial licenses if True."),
    db: Session = Depends(get_db)
):
    """
    Returns the top 3 recommended LLMs for a chosen profile.
    Calculates dynamic composite scores per query based on profile weights.
    """
    try:
        recommendations = get_recommendations(db, profile=profile, commercial_only=commercial, top_k=3)
        return {
            "profile": profile,
            "commercial_only": commercial,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
