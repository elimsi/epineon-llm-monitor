# 📡 Data Sources Documentation

> **Module 1 — Task T5**: Document the sources used, their update frequency, and any limitations encountered.
> 
> **Author**: EL KHOBZI Ismail · ESITH Technical Challenge 2026

---

## Source 1: Artificial Analysis (`artificialanalysis.ai`)

| Field | Details |
|-------|---------|
| **URL** | https://artificialanalysis.ai |
| **Data Extracted** | Intelligence score, pricing (input/output per 1M tokens), speed (tokens/s), TTFT latency, context window |
| **Update Frequency** | Continuously updated; we snapshot weekly |
| **Coverage** | ~30 commercial and open-source models |
| **Limitations** | No public REST API — data compiled manually from their leaderboard pages. Some smaller models are missing. Speed benchmarks vary by provider and may not reflect all deployment configurations. |

---

## Source 2: LMSYS Chatbot Arena (`lmarena.ai`)

| Field | Details |
|-------|---------|
| **URL** | https://lmarena.ai/leaderboard |
| **Data Extracted** | Arena ELO ratings (human preference voting) |
| **Update Frequency** | Rolling — updated after each voting session (~hourly) |
| **Coverage** | ~100+ models with ELO ratings |
| **Limitations** | ELO ratings can fluctuate with new votes. Some models (especially small/niche ones) may have insufficient votes for a stable rating. We capture the "Overall" ELO, not per-category breakdowns. ELO is relative — new entrants may temporarily have inflated or deflated scores. |

---

## Source 3: HuggingFace Open LLM Leaderboard

| Field | Details |
|-------|---------|
| **URL** | https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard |
| **Data Extracted** | Benchmark scores for open-source models (MMLU, HellaSwag, ARC, etc.), license type, model size |
| **Update Frequency** | Community-driven — new submissions evaluated within days |
| **Coverage** | Open-source models only (Llama, Mistral, Qwen, Gemma, Phi, etc.) |
| **Limitations** | Only covers open-weight models — no proprietary models (GPT, Claude, Gemini). Benchmark scores are not directly comparable to Artificial Analysis "intelligence score" — we normalize to a 0–100 scale. Some models may game specific benchmarks. |

---

## Source 4: OpenRouter (`openrouter.ai`)

| Field | Details |
|-------|---------|
| **URL** | https://openrouter.ai/models |
| **Data Extracted** | Real-time API pricing (input/output per token), available providers, context window |
| **Update Frequency** | Real-time — prices reflect current market rates |
| **Coverage** | 200+ models across multiple providers |
| **Limitations** | Prices vary by provider (e.g., same model hosted on different infra). We take the median price. Speed/latency depend on the specific provider and load, not just the model. Free-tier pricing may not be representative. |

---

## Normalization Strategy

All metrics are normalized to a **0–100 scale** using **min-max normalization** computed dynamically at query time:

```
normalized = (value - min) / (max - min)
```

- **Cost** and **Latency** use **reverse normalization** (lower = better score)
- **Intelligence**, **ELO**, **Speed**, **Context** use standard normalization (higher = better)
- Missing values default to the midpoint (0.5) to avoid penalizing incomplete data

This approach ensures scores are always relative to the current dataset, automatically adjusting as new models are added or prices change.

---

## Data Freshness & Snapshot Date

| Property | Value |
|----------|-------|
| **Current snapshot** | March 2026 |
| **Total models tracked** | 39 |
| **Automated refresh** | Every 24 hours via APScheduler |
| **Storage** | SQLite (`llm_monitor_v2.db`) via SQLAlchemy |

---

*This document satisfies Module 1, Task T5 of the ESITH Challenge 2026.*
