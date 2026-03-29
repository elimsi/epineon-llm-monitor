import numpy as np
import math
from sqlalchemy.orm import Session
from .models import LLMModel

# Enterprise Profile Weights (Priorities)
# Format: [Intelligence, Arena ELO, Price, Speed, Latency, Context Window]
PROFILES = {
    "Coding/Dev": [0.35, 0.15, 0.10, 0.20, 0.15, 0.05],
    "Reasoning/Analysis": [0.45, 0.20, 0.10, 0.05, 0.15, 0.05],
    "Minimum Cost": [0.05, 0.05, 0.70, 0.05, 0.10, 0.05],
    "Enterprise Agents": [0.25, 0.15, 0.15, 0.15, 0.20, 0.10],
    "Balanced": [0.20, 0.15, 0.20, 0.15, 0.20, 0.10]
}

def calculate_entropy_weights(matrix: np.ndarray) -> np.ndarray:
    """Calculates objective weights using Shannon Entropy."""
    rows, cols = matrix.shape
    # Normalization (Min-Max)
    norm_matrix = (matrix - matrix.min(axis=0)) / (matrix.max(axis=0) - matrix.min(axis=0) + 1e-9)
    # Probability distribution
    p = norm_matrix / (norm_matrix.sum(axis=0) + 1e-9)
    # Entropy E_j
    k = 1.0 / math.log(rows) if rows > 1 else 1.0
    entropy = -k * np.sum(p * np.log(p + 1e-9), axis=0)
    # Dispersion D_j
    dispersion = 1 - entropy
    # Weights w_j
    return dispersion / (dispersion.sum() + 1e-9)

def get_recommendations(db: Session, profile: str = "Balanced", 
                        prompt_tokens: int = 1000, 
                        completion_tokens: int = 1000,
                        top_k: int = 10):
    
    models = db.query(LLMModel).all()
    if not models: return []

    # 1. Prepare Decision Matrix
    # Criteria: [Intel, ELO, Price(Inv), Speed, Latency(Inv), Ctx]
    matrix = []
    for m in models:
        # We invert Cost and Latency because lower is better for them (Beneficial Criteria)
        # VIKOR handles minimization vs maximization differently, but Min-Max norm is standard
        intel = m.intelligence_score or 50.0
        elo = m.arena_elo or 1000
        cost = (m.price_input_token * prompt_tokens + m.price_output_token * completion_tokens) or 1.0
        speed = m.speed_tokens_per_sec or 10.0
        ttft = m.ttft_latency or 1.0
        ctx = m.context_window or 8192
        
        matrix.append([intel, elo, 1/cost, speed, 1/ttft, ctx])

    matrix = np.array(matrix)
    
    # 2. Hybrid Weighting (Enterprise Priority * Data-Driven Entropy)
    entropy_weights = calculate_entropy_weights(matrix)
    enterprise_weights = np.array(PROFILES.get(profile, PROFILES["Balanced"]))
    final_weights = entropy_weights * enterprise_weights
    final_weights /= final_weights.sum()

    # 3. VIKOR Ranking
    # Normalization (Best/Worst) for breakdown scaling
    f_star = matrix.max(axis=0)
    f_minus = matrix.min(axis=0)
    
    # Calculate normalized matrix for radar chart values 0-100
    norm_matrix = (matrix - f_minus) / (f_star - f_minus + 1e-9) * 100

    # Calculate S (Utility) and R (Regret)
    S = np.zeros(matrix.shape[0])
    R = np.zeros(matrix.shape[0])

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = final_weights[j] * (f_star[j] - matrix[i,j]) / (f_star[j] - f_minus[j] + 1e-9)
            S[i] += val
            R[i] = max(R[i], val)

    S_star, S_minus = S.min(), S.max()
    R_star, R_minus = R.min(), R.max()

    # Calculate Q (Final VIKOR Index) - Balance S and R (v=0.5)
    v = 0.5
    Q = v * (S - S_star) / (S_minus - S_star + 1e-9) + (1 - v) * (R - R_star) / (R_minus - R_star + 1e-9)

    # 4. Format Results
    results = []
    for idx, model in enumerate(models):
        score = round(float(100 - (Q[idx] * 100)), 2) # Mapping VIKOR Q (min is best) to 0-100 (max is best)
        results.append({
            "model_name": model.name,
            "score": score,
            "intelligence_score": model.intelligence_score,
            "arena_elo": model.arena_elo,
            "price_input": model.price_input_token,
            "price_output": model.price_output_token,
            "speed_tokens_sec": model.speed_tokens_per_sec,
            "ttft_latency": model.ttft_latency,
            "context_window": model.context_window,
            "justification": f"Compromise solution between Intelligence and Cost for {profile}.",
            "breakdown": {
                "intel": round(float(norm_matrix[idx,0]), 2),
                "elo": round(float(norm_matrix[idx,1]), 2),
                "cost_score": round(float(norm_matrix[idx,2]), 2),
                "speed": round(float(norm_matrix[idx,3]), 2),
                "latency": round(float(norm_matrix[idx,4]), 2),
                "ctx": round(float(norm_matrix[idx,5]), 2)
            }
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]
