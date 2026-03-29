"""
Module 2A: Scoring & Recommendation Engine
==========================================
Calculates composite scores using weighted normalization across 6 dimensions:
  - Intelligence (benchmark scores)
  - Arena ELO (human preference ratings from LMSYS Arena)
  - Cost (pricing per 1M tokens, lower = better)
  - Speed (output tokens/second)
  - Latency (time to first token, lower = better)
  - Context window size

Profiles configure different weight distributions for Enterprise use-cases.
Each recommendation includes a justification explaining why the model was chosen.
"""

from sqlalchemy.orm import Session
from models import LLMModel

# ═══════════════════════════════════════════════════════════════
# ENTERPRISE PROFILES — Weighted scoring presets
# All weights must sum to 1.0
# ═══════════════════════════════════════════════════════════════

PROFILES = {
    "Coding/Dev": {
        "description": "Optimized for code generation, debugging, and technical reasoning",
        "intelligence_weight": 0.45,
        "arena_weight": 0.15,
        "cost_weight": 0.10,
        "speed_weight": 0.10,
        "latency_weight": 0.05,
        "context_weight": 0.15,
    },
    "Reasoning/Analysis": {
        "description": "Maximum reasoning depth for research, strategy, and complex analysis",
        "intelligence_weight": 0.40,
        "arena_weight": 0.25,
        "cost_weight": 0.05,
        "speed_weight": 0.05,
        "latency_weight": 0.0,
        "context_weight": 0.25,
    },
    "Minimum Cost": {
        "description": "Budget-optimized for high-volume, cost-sensitive workloads",
        "intelligence_weight": 0.15,
        "arena_weight": 0.05,
        "cost_weight": 0.65,
        "speed_weight": 0.10,
        "latency_weight": 0.05,
        "context_weight": 0.0,
    },
    "Enterprise Agents": {
        "description": "Low-latency, fast models for agentic tool-use and automation",
        "intelligence_weight": 0.20,
        "arena_weight": 0.15,
        "cost_weight": 0.10,
        "speed_weight": 0.30,
        "latency_weight": 0.25,
        "context_weight": 0.0,
    },
    "Balanced": {
        "description": "Equal weight across all dimensions — general-purpose baseline",
        "intelligence_weight": 0.20,
        "arena_weight": 0.15,
        "cost_weight": 0.20,
        "speed_weight": 0.15,
        "latency_weight": 0.15,
        "context_weight": 0.15,
    },
}


def normalize(value, min_val, max_val, reverse=False):
    """Normalize a value to a 0-1 scale. If reverse=True, lower values get higher scores."""
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    return 1 - normalized if reverse else normalized


def calculate_composite_score(model: LLMModel, profile_name: str, metrics_ranges: dict) -> dict:
    """
    Calculates the composite score based on the selected profile's weights.
    Returns a dict with the total score AND dimension breakdown for justification.
    """
    weights = PROFILES.get(profile_name)
    if not weights:
        return {"score": 0.0, "breakdown": {}}

    # Handle missing metrics safely
    intel   = model.intelligence_score or 0
    elo     = model.arena_elo or metrics_ranges.get("min_elo", 1000)
    price   = (model.price_input_token or 0) + (model.price_output_token or 0)
    speed   = model.speed_tokens_per_sec or 0
    latency = model.ttft_latency or 10.0
    context = model.context_window or 0

    norm_intel   = normalize(intel,   metrics_ranges["min_intel"],   metrics_ranges["max_intel"])
    norm_elo     = normalize(elo,     metrics_ranges["min_elo"],     metrics_ranges["max_elo"])
    norm_cost    = normalize(price,   metrics_ranges["min_cost"],    metrics_ranges["max_cost"],    reverse=True)
    norm_speed   = normalize(speed,   metrics_ranges["min_speed"],   metrics_ranges["max_speed"])
    norm_latency = normalize(latency, metrics_ranges["min_latency"], metrics_ranges["max_latency"], reverse=True)
    norm_context = normalize(context, metrics_ranges["min_context"], metrics_ranges["max_context"])

    # Weighted sum
    score = (
        (norm_intel   * weights["intelligence_weight"]) +
        (norm_elo     * weights["arena_weight"]) +
        (norm_cost    * weights["cost_weight"]) +
        (norm_speed   * weights["speed_weight"]) +
        (norm_latency * weights["latency_weight"]) +
        (norm_context * weights["context_weight"])
    )

    breakdown = {
        "intelligence": round(norm_intel * 100, 1),
        "arena_elo":    round(norm_elo * 100, 1),
        "cost":         round(norm_cost * 100, 1),
        "speed":        round(norm_speed * 100, 1),
        "latency":      round(norm_latency * 100, 1),
        "context":      round(norm_context * 100, 1),
    }

    return {"score": round(score * 100, 2), "breakdown": breakdown}


def generate_justification(model_data: dict, profile_name: str) -> str:
    """Generate a human-readable justification for why a model was recommended."""
    bd = model_data["breakdown"]
    profile = PROFILES[profile_name]
    
    # Find top 2 contributing dimensions
    weighted_dims = {
        "intelligence": bd["intelligence"] * profile["intelligence_weight"],
        "arena_elo":    bd["arena_elo"]    * profile["arena_weight"],
        "affordability":bd["cost"]         * profile["cost_weight"],
        "speed":        bd["speed"]        * profile["speed_weight"],
        "low_latency":  bd["latency"]      * profile["latency_weight"],
        "context_size": bd["context"]      * profile["context_weight"],
    }
    top_dims = sorted(weighted_dims.items(), key=lambda x: x[1], reverse=True)[:2]
    
    top_names = [d[0].replace("_", " ").title() for d in top_dims]
    return f"Ranked highly due to exceptional {top_names[0]} and {top_names[1]} for the {profile_name} profile."


def get_recommendations(db: Session, profile: str, commercial_only: bool = False, top_k: int = 5):
    """Returns the top K recommended LLMs for a specific profile with justifications."""
    if profile not in PROFILES:
        raise ValueError(f"Profile '{profile}' not found. Available: {list(PROFILES.keys())}")

    models_query = db.query(LLMModel)
    
    if commercial_only:
        models_query = models_query.filter(~LLMModel.license_type.ilike('%non-commercial%'))

    all_models = models_query.all()
    if not all_models:
        return []

    # Calculate ranges dynamically for normalization
    def safe_min(vals):
        filtered = [v for v in vals if v is not None]
        return min(filtered) if filtered else 0
    def safe_max(vals):
        filtered = [v for v in vals if v is not None]
        return max(filtered) if filtered else 1

    ranges = {
        "min_intel":   safe_min(m.intelligence_score for m in all_models),
        "max_intel":   safe_max(m.intelligence_score for m in all_models),
        "min_elo":     safe_min(m.arena_elo for m in all_models),
        "max_elo":     safe_max(m.arena_elo for m in all_models),
        "min_cost":    safe_min((m.price_input_token or 0) + (m.price_output_token or 0) for m in all_models),
        "max_cost":    safe_max((m.price_input_token or 0) + (m.price_output_token or 0) for m in all_models),
        "min_speed":   safe_min(m.speed_tokens_per_sec for m in all_models),
        "max_speed":   safe_max(m.speed_tokens_per_sec for m in all_models),
        "min_latency": safe_min(m.ttft_latency for m in all_models),
        "max_latency": safe_max(m.ttft_latency for m in all_models),
        "min_context": safe_min(m.context_window for m in all_models),
        "max_context": safe_max(m.context_window for m in all_models),
    }

    scored_models = []
    for m in all_models:
        result = calculate_composite_score(m, profile, ranges)
        model_data = {
            "model_name":           m.name,
            "score":                result["score"],
            "breakdown":            result["breakdown"],
            "license":              m.license_type,
            "intelligence_score":   m.intelligence_score,
            "arena_elo":            m.arena_elo,
            "cost_per_1m_tokens":   round((m.price_input_token or 0) + (m.price_output_token or 0), 2),
            "price_input":          m.price_input_token,
            "price_output":         m.price_output_token,
            "previous_cost":        round((m.previous_price_input or 0) + (m.previous_price_output or 0), 2) if m.previous_price_input else None,
            "speed_tokens_sec":     m.speed_tokens_per_sec,
            "ttft_latency":         m.ttft_latency,
            "context_window":       m.context_window,
            "data_source":          m.data_source,
            "first_seen":           m.first_seen.isoformat() if m.first_seen else None,
            "last_updated":         m.last_updated.isoformat() if m.last_updated else None,
        }
        model_data["justification"] = generate_justification(model_data, profile)
        scored_models.append(model_data)

    scored_models.sort(key=lambda x: x["score"], reverse=True)
    return scored_models[:top_k]
