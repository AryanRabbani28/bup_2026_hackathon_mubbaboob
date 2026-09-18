# 3-Minute Presentation & Architecture Video Script

**Target Duration**: 2 minutes 45 seconds to 3 minutes  
**Goal**: Clearly communicate problem understanding, pipeline architecture, Gemini interpretation with deterministic guardrails, mathematical optimization, and independent verification.

---

### [0:00 - 0:30] Introduction & Problem Understanding
- **Visual**: Title slide showing "GridWise: LLM-Assisted Smart Campus Energy Optimization — BUP CSE Fest 2026", followed by screen recording of the repo.
- **Voiceover**: 
  "Hello judges! This is our solution for the GridWise Smart Campus Energy Optimization Challenge. Smart campuses generate rooftop solar, use battery storage, and draw electricity from the grid with hourly time-of-day tariffs. On top of 24-hour demand and solar forecasts, campus operators frequently send unpredictable natural-language notes—such as maintenance windows, inverter reductions, or reserve requirements—along with distractor notes. Our mission is to accurately interpret these unstructured human notes, apply them deterministically, and compute a globally optimal, physically valid 24-hour schedule."

---

### [0:30 - 1:15] The Core Architecture & Gemini Guardrails
- **Visual**: Architecture diagram from `docs/architecture.md` (Request -> Validation -> Gemini -> Guardrails -> Optimizer -> Validator -> Response).
- **Voiceover**:
  "Our architecture strictly decouples natural language understanding from mathematical scheduling. 
  First, Pydantic validates the incoming payload, verifying exactly 24 hourly intervals and consistent battery limits.
  Second, our Gemini Interpreter uses Google's latest Gemini 3.5 Flash model with REST transport and strict structured output. In a single call, it extracts machine-readable directives across all operator notes, adhering to whole-hour start-inclusive, end-exclusive windows.
  Third, we treat LLM output as untrusted until validated by our deterministic guardrails. Our validator checks note indexing, applies semantics, unique sorted hours, solar reduction bounds between 0 and 1, and non-negative reserve limits. Any invalid output triggers automated error-guided repair."

---

### [1:15 - 2:00] Mathematical Optimizer & Independent Verification
- **Visual**: Showing `backend/app/optimization/optimizer.py` and `backend/app/validation/schedule_validator.py`.
- **Voiceover**:
  "Once validated, directives are compiled into constraints for an exact linear programming model using `scipy.optimize.linprog` with the state-of-the-art HiGHS solver. By formulating signed continuous battery flows, we guarantee exact energy balance and cost minimization without unnecessary mixed-integer heuristics.
  Crucially, we never trust the solver blindly. A separate Independent Schedule Validator replays the entire 24-hour schedule hour-by-hour. It verifies energy balance, battery capacity bounds, charge and discharge limits, reserve directives, no-charge/no-discharge windows, grid import caps, and mandatory end-of-day battery neutrality."

---

### [2:00 - 2:45] Testing, Public Sample Validation & Deployment
- **Visual**: Terminal showing `pytest` passing 12/12 tests, followed by running `python scripts/run_public_samples.py` showing 10/10 passed cases, then showing the Docker build and frontend.
- **Voiceover**:
  "Here in our terminal, you can see all 12 unit and optimizer tests passing in under 2 seconds. 
  When we run our public test runner against our live API, all 10 official public sample cases pass with 100% semantic accuracy and exact optimal costs matching the judge reference.
  Our backend is packaged with a clean, unauthenticated `/health` check and production `Dockerfile` ready for Render, paired with a modern React/Vite dashboard deployable on Vercel. Thank you!"
