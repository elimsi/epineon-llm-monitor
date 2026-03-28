from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    intelligence_score = Column(Float, nullable=True) # Normalized 0-100
    price_input_token = Column(Float, nullable=True) # Per 1M tokens
    price_output_token = Column(Float, nullable=True) # Per 1M tokens
    speed_tokens_per_sec = Column(Float, nullable=True)
    ttft_latency = Column(Float, nullable=True) # Time To First Token
    context_window = Column(Integer, nullable=True)
    license_type = Column(String, nullable=True)
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Check if a model is "newly detected" by comparing last_updated
