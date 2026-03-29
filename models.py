from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Core performance metrics
    intelligence_score = Column(Float, nullable=True)       # Normalized 0-100 (from benchmarks)
    arena_elo = Column(Integer, nullable=True)              # LMSYS Chatbot Arena ELO rating
    
    # Pricing (per 1M tokens, in USD)
    price_input_token = Column(Float, nullable=True)
    price_output_token = Column(Float, nullable=True)
    previous_price_input = Column(Float, nullable=True)     # For tracking price drops
    previous_price_output = Column(Float, nullable=True)    # For tracking price drops
    
    # Speed & latency
    speed_tokens_per_sec = Column(Float, nullable=True)     # Output tokens per second
    ttft_latency = Column(Float, nullable=True)             # Time To First Token (seconds)
    
    # Capacity
    context_window = Column(Integer, nullable=True)         # Max tokens
    
    # Licensing
    license_type = Column(String, nullable=True)            # Proprietary, Apache 2.0, MIT, etc.
    
    # Tracking
    first_seen = Column(DateTime, default=datetime.utcnow)  # When this model was first added
    last_updated = Column(DateTime, default=datetime.utcnow) # Last data refresh
    
    # Data source attribution
    data_source = Column(String, nullable=True)             # e.g. "Artificial Analysis, LMSYS Arena"
