from sqlalchemy.orm import Session
from models import LLMModel

# Define enterprise profiles and their custom weights.
# The formula calculates a final score out of 100 based on these metrics.
# Important metrics depend heavily on the profile chosen.
#
# Weights breakdown (out of 1.0):
# - intelligence_score (Higher is better)
# - cost (price_input + price_output) (Lower is better)
# - speed (speed_tokens_per_sec) (Higher is better)
# - latency (ttft_latency) (Lower is better)
# - context (context_window) (Higher is better)

PROFILES = {
    "Coding/Dev": {
        "intelligence_weight": 0.60,
        "cost_weight": 0.10,
        "speed_weight": 0.10,
        "latency_weight": 0.05,
        "context_weight": 0.15,
    },
    "Reasoning/Analysis": {
        "intelligence_weight": 0.70,
        "cost_weight": 0.05,
        "speed_weight": 0.05,
        "latency_weight": 0.0,
        "context_weight": 0.20,
    },
    "Minimum Cost": {
        "intelligence_weight": 0.20,
        "cost_weight": 0.70,
        "speed_weight": 0.05,
        "latency_weight": 0.05,
        "context_weight": 0.0,
    },
    "Enterprise Agents": {
        "intelligence_weight": 0.30,
        "cost_weight": 0.10,
        "speed_weight": 0.30,
        "latency_weight": 0.30,
        "context_weight": 0.0,
    }
}

def normalize(value, min_val, max_val, reverse=False):
    """Normalize a value to a 0-1 scale. If reverse=True, lower values get higher scores."""
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    return 1 - normalized if reverse else normalized

def calculate_composite_score(model: LLMModel, profile_name: str, metrics_ranges: dict) -> float:
    """Calculates the composite score based on the selected profile's weights."""
    weights = PROFILES.get(profile_name)
    if not weights:
        return 0.0

    # Handle missing metrics safely
    intel = model.intelligence_score or 0
    price = (model.price_input_token or 0) + (model.price_output_token or 0)
    speed = model.speed_tokens_per_sec or 0
    latency = model.ttft_latency or 10.0
    context = model.context_window or 0

    norm_intel = normalize(intel, metrics_ranges["min_intel"], metrics_ranges["max_intel"])
    norm_cost = normalize(price, metrics_ranges["min_cost"], metrics_ranges["max_cost"], reverse=True)
    norm_speed = normalize(speed, metrics_ranges["min_speed"], metrics_ranges["max_speed"])
    norm_latency = normalize(latency, metrics_ranges["min_latency"], metrics_ranges["max_latency"], reverse=True)
    norm_context = normalize(context, metrics_ranges["min_context"], metrics_ranges["max_context"])

    score = (
        (norm_intel * weights["intelligence_weight"]) +
        (norm_cost * weights["cost_weight"]) +
        (norm_speed * weights["speed_weight"]) +
        (norm_latency * weights["latency_weight"]) +
        (norm_context * weights["context_weight"])
    )

    return round(score * 100, 2)

def get_recommendations(db: Session, profile: str, commercial_only: bool = False, top_k: int = 3):
    """Returns the top K recommended LLMs for a specific profile."""
    if profile not in PROFILES:
        raise ValueError(f"Profile {profile} not found. Available: {list(PROFILES.keys())}")

    models_query = db.query(LLMModel)
    
    if commercial_only:
        # MIT, Apache 2.0, etc., are standard commercial friendly open source. 
        # (Assuming ' Proprietary' allows commercial usage via API)
        # Any 'Non-Commercial' string would be filtered out.
        models_query = models_query.filter(~LLMModel.license_type.ilike('%non-commercial%'))

    all_models = models_query.all()
    if not all_models:
        return []

    # Calculate ranges dynamically for proper normalization
    ranges = {
        "min_intel": min(m.intelligence_score for m in all_models if m.intelligence_score) or 0,
        "max_intel": max(m.intelligence_score for m in all_models if m.intelligence_score) or 100,
        "min_cost": min((m.price_input_token or 0) + (m.price_output_token or 0) for m in all_models),
        "max_cost": max((m.price_input_token or 0) + (m.price_output_token or 0) for m in all_models),
        "min_speed": min(m.speed_tokens_per_sec for m in all_models if m.speed_tokens_per_sec) or 0,
        "max_speed": max(m.speed_tokens_per_sec for m in all_models if m.speed_tokens_per_sec) or 1000,
        "min_latency": min(m.ttft_latency for m in all_models if m.ttft_latency) or 0,
        "max_latency": max(m.ttft_latency for m in all_models if m.ttft_latency) or 5.0,
        "min_context": min(m.context_window for m in all_models if m.context_window) or 0,
        "max_context": max(m.context_window for m in all_models if m.context_window) or 128000,
    }

    scored_models = []
    for m in all_models:
        score = calculate_composite_score(m, profile, ranges)
        scored_models.append({
            "model_name": m.name,
            "score": score,
            "license": m.license_type,
            "intelligence_score": m.intelligence_score,
            "cost_per_1m_tokens": (m.price_input_token or 0) + (m.price_output_token or 0),
            "speed_tokens_sec": m.speed_tokens_per_sec,
            "context_window": m.context_window
        })

    # Sort descending based on score
    scored_models.sort(key=lambda x: x["score"], reverse=True)
    return scored_models[:top_k]
