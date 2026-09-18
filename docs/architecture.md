# GridWise System Architecture

## Overview
The GridWise system optimizes 24-hour campus energy schedules combining grid electricity, rooftop solar generation, and battery energy storage. In addition to numerical time-series forecasts, it processes 1–3 natural-language operator notes describing temporary constraints or distractor messages.

## End-to-End Pipeline

```text
Request (JSON)
  │
  ▼
[Pydantic Schema Validation] 
  │  - Ensures exactly 24 unique hourly entries (0..23)
  │  - Validates battery parameters and non-negative constraints
  ▼
[Gemini Operator-Note Interpreter]
  │  - Extracts semantic intent for every operator note using Gemini 3.5 Flash
  │  - Maps notes strictly to 1 of 6 allowed directive types or `no_op`
  │  - Outputs structured adjustments with inclusive-start, exclusive-end hours
  ▼
[Deterministic Guardrails]
  │  - Enforces note indexing (0..N-1) and applies semantics
  │  - Validates hours are unique, sorted integers in [0, 23]
  │  - Verifies numeric ranges (solar factor in [0, 1], non-negative reserves/caps)
  ▼
[Linear Program Optimizer (SciPy HiGHS)]
  │  - Compiles directives into linear constraints and adjusted bounds
  │  - Formulates continuous 24-hour LP with signed battery flow
  │  - Minimizes total grid electricity cost: Σ(grid_kwh[h] * tariff[h])
  ▼
[Independent Schedule Replayer & Validator]
  │  - Separate verification engine from optimizer
  │  - Replays hour-by-hour physics, rate limits, energy balance, and bounds
  │  - Guarantees end-of-day battery neutrality (E_23 == E_initial)
  ▼
[Recalculated Totals & Response]
  │  - Independently derived total_grid_kwh, total_cost_bdt, peak_grid_kwh
  │  - Generates deterministic plan_summary
  ▼
Response (JSON)
```

## Key Components

1. **`app/api/models.py`**: Pydantic v2 data models for request/response serialization and strict typing.
2. **`app/llm/interpreter.py`**: Uses Google Gemini Generative AI (with REST transport) to interpret natural language. Implements prompt engineering, automated repairs, retry backoffs, and fallback models (`gemini-3.5-flash-lite`).
3. **`app/validation/directive_validator.py`**: Hard deterministic guardrails validating model output before mathematical scheduling.
4. **`app/optimization/optimizer.py`**: Fast, exact linear program using `scipy.optimize.linprog(method="highs")`. Reconstructs exact battery charge/discharge actions and states.
5. **`app/validation/schedule_validator.py`**: Independent replayer verifying 20 distinct physical and logical constraints.
6. **`app/services/optimization_service.py`**: Orchestrates the pipeline stages cleanly and safely.
