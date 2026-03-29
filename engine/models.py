from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Core performance metrics
    intelligence_score = Column(Float, nullable=True)
    arena_elo = Column(Integer, nullable=True)
    
    # Pricing (per 1M tokens)
    price_input_token = Column(Float, nullable=True)
    price_output_token = Column(Float, nullable=True)
    previous_price_input = Column(Float, nullable=True)
    previous_price_output = Column(Float, nullable=True)
    
    # Speed & latency
    speed_tokens_per_sec = Column(Float, nullable=True)
    ttft_latency = Column(Float, nullable=True)
    
    # Capacity
    context_window = Column(Integer, nullable=True)
    
    # Licensing
    license_type = Column(String, nullable=True)
    
    # Tracking
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Data source attribution
    data_source = Column(String, nullable=True)
