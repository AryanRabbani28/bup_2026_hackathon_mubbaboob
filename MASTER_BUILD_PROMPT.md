# MASTER BUILD PROMPT — BUP CSE FEST 2026 GridWise LLM Hackathon

## Role

You are the lead engineer for a time-constrained hackathon implementation.

Your job is to design, then after explicit approval implement, a complete submission-ready solution for the **BUP CSE FEST 2026 Hackathon — GridWise LLM-Assisted Smart Campus Energy Optimization Challenge**.

This repository is currently effectively empty except for the already-installed Ponytail-related repository/tooling. Before making any plan, inspect the repository root and read every project-level instruction file that exists, including any `AGENTS.md`, Ponytail instructions/configuration, README, editor/agent rules, or project metadata. Follow those local instructions unless they conflict with the official hackathon documents. Do not assume any Ponytail behavior that is not actually present in the repository.

The official challenge materials are the source of truth:

1. `BUP_CSE_FEST_2026_Preliminary_Problem_Statement_GridWise_LLM.pdf`
2. `BUP_CSE_FEST_2026_Participant_Guide_&_Evaluation_Rubric_GridWise_LLM.pdf`
3. `BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json`

If these documents are available in the workspace, read them directly before planning. If this prompt and an official challenge document appear to disagree, follow the official challenge document.

### Canonical-source hierarchy

- The **Problem Statement** is canonical for endpoint names, request/response schema, operator-note directive types, interpretation rules and guardrails, battery behavior, energy accounting, and optimization validity.
- The **Participant Guide & Evaluation Rubric** is canonical for deployment, repository policy, submission, performance, scoring, penalties, and tie-break rules.
- The **Public Sample Cases JSON** is for local validation and examples. It is **not** the hidden judge set and must never be hard-coded into production logic.

---

# PHASE GATE — VERY IMPORTANT

This project uses a checkpoint workflow.

## Phase A — PLAN ONLY

For the first response after receiving this prompt:

**DO NOT IMPLEMENT ANYTHING. DO NOT MODIFY FILES. DO NOT INSTALL DEPENDENCIES. DO NOT WRITE CODE.**

Instead:

1. Inspect the repository and local agent/Ponytail instructions.
2. Read the three official challenge files.
3. Produce a detailed implementation plan.
4. Show:
   - architecture
   - file/folder structure
   - request/response models
   - Gemini integration
   - deterministic LLM guardrails
   - optimization formulation
   - independent schedule validator design
   - retry/fallback policy
   - local test strategy
   - public-sample runner design
   - Docker plan
   - Render backend deployment plan
   - Vercel frontend plan
   - environment variables
   - error-handling strategy
   - latency strategy
   - security strategy
   - assumptions or ambiguities found in the official documents
   - implementation order optimized for the scoring rubric and limited hackathon time
5. Explicitly list any behavior where the official documents do not define an unambiguous rule. Do not silently invent semantics.
6. End by waiting for my approval.

Do not proceed beyond planning until I explicitly approve the plan.

## Phase B — IMPLEMENT AFTER APPROVAL

After I say the plan is approved, execute it completely.

Do not repeatedly stop for confirmation during implementation unless:
- a credential is required,
- an external deployment requires my authentication,
- a genuine ambiguity in the official challenge specification blocks a correct implementation,
- or an irreversible/destructive action is required.

After approval, continue through coding, tests, debugging, Docker, documentation, and deployment preparation until the acceptance criteria in this document are satisfied.

---

# 1. PRODUCT GOAL

Build one complete system that accepts a 24-hour smart-campus energy scenario and 1–3 natural-language operator notes.

The service must:

1. Use a **Gemini language model** to interpret every operator note.
2. Convert each note into exactly one supported machine-readable directive.
3. Deterministically validate the LLM output.
4. Apply all valid directives to a 24-hour energy optimization problem.
5. Produce a valid low-cost schedule using grid electricity, rooftop solar, and battery storage.
6. Independently replay and validate the final schedule.
7. Return the exact required JSON response.
8. Remain reliable, secure, reproducible, and deployable.

The conceptual pipeline must be:

```text
Request
  ↓
Input validation
  ↓
Gemini operator-note interpretation
  ↓
Deterministic directive guardrails
  ↓
Directive application
  ↓
Mathematical optimizer
  ↓
Independent final schedule validator/replayer
  ↓
Totals recalculation
  ↓
Exact API response
```

Do not merge the LLM and optimizer into one opaque call.

The LLM understands language. Deterministic code validates language-model output. The optimizer performs mathematical scheduling. A separate deterministic validator independently checks optimizer output.

---

# 2. PRIORITY ORDER

Hackathon time is limited. Follow this priority order unless the official documents require otherwise:

1. Exact API and JSON contract
2. Correct Gemini operator-note interpretation
3. Deterministic guardrails
4. Correct directive application
5. Energy and battery correctness
6. Independent final validation
7. Optimization cost quality
8. Reliability and latency
9. Render deployment
10. Docker fallback
11. README and reproducibility
12. Local public-sample runner
13. Minimal Vercel frontend
14. Video/tie-break material

Do not spend time polishing the frontend while scoring-critical backend behavior is incomplete.

---

# 3. REQUIRED TECHNOLOGY

Use:

- **Python**
- **FastAPI**
- **Pydantic**
- **Gemini API**
- A deterministic mathematical optimization library suitable for a small 24-hour problem
- **pytest**
- **Docker**
- **Render** for the public backend
- **Vercel** for a lightweight frontend

Preferred optimizer unless the planning phase finds a concrete reason to use something else:

- `scipy.optimize.linprog(method="highs")`

Reason:
- the problem can be expressed as a small linear program,
- it avoids unnecessary mixed-integer complexity,
- it is fast,
- it is reproducible,
- it simplifies Docker/Render deployment.

During Phase A verify this formulation against the official problem statement before committing to it.

Do not use a heuristic when an exact small linear program is practical.

---

# 4. REQUIRED API

Build exactly one backend service.

## GET `/health`

When ready:

- HTTP 200
- JSON:

```json
{
  "status": "ok"
}
```

The health route must be lightweight. Do not perform a Gemini call in `/health`.

## POST `/optimize-energy`

Accept one scenario object and return:
- the LLM-derived machine-readable interpretation,
- the optimized 24-hour energy plan,
- recalculated totals,
- a short plan summary.

Use the exact official field names.

---

# 5. REQUEST CONTRACT

Top-level request fields:

```text
scenario_id
operator_notes
hours
battery
```

Requirements:

- `operator_notes` contains 1–3 non-empty natural-language strings.
- `hours` contains exactly 24 entries.
- Hours represent exactly `0` through `23`.

Each hour contains:

```text
hour
demand_kwh
solar_kwh
tariff_bdt_per_kwh
```

Battery contains:

```text
capacity_kwh
initial_energy_kwh
minimum_energy_kwh
max_charge_kwh_per_hour
max_discharge_kwh_per_hour
```

Input validation must reject malformed/structurally invalid inputs safely.

Do not over-restrict hidden cases with assumptions that are not supported by the official specification.

All required numeric values must be finite.

---

# 6. SUPPORTED DIRECTIVE TYPES

The LLM may produce only the following directive types.

## 6.1 `solar_reduction`

Meaning: reduce usable solar during listed hours.

Required structured adjustment:

```json
{
  "hours": [13, 14],
  "factor": 0.2
}
```

Important: `factor` is the usable fraction remaining.

Example: "Solar is reduced by 80%" means `factor = 0.2`, not `0.8`.

Deterministic effect:

```text
effective_solar[h] = original_solar[h] * factor
```

for each affected hour.

## 6.2 `minimum_battery_reserve`

Meaning: battery energy must remain at or above a specified reserve during listed hours.

Required structured adjustment:

```json
{
  "hours": [18, 19, 20],
  "minimum_energy_kwh": 120
}
```

Deterministic effect:

```text
battery_energy_after_kwh[h]
>= max(base minimum_energy_kwh, active directive reserve)
```

for each affected hour.

## 6.3 `no_charge_window`

Required adjustment:

```json
{
  "hours": [14, 15]
}
```

Battery charging must equal zero for listed hours.

## 6.4 `no_discharge_window`

Required adjustment:

```json
{
  "hours": [17, 18]
}
```

Battery discharging must equal zero for listed hours.

## 6.5 `max_grid_window`

Required adjustment:

```json
{
  "hours": [19, 20],
  "max_grid_kwh": 180
}
```

Constraint:

```text
grid_kwh[h] <= max_grid_kwh
```

for each listed hour.

## 6.6 `no_op`

Use when the note does not affect the current 24-hour energy schedule.

Must use:

```json
{
  "applies": false,
  "directive_type": "no_op",
  "structured_adjustment": null
}
```

`no_op` is the only directive allowed to use `applies = false`.

Every other supported directive must use `applies = true`.

---

# 7. TIME-WINDOW NORMALIZATION

Time windows are:

- start-inclusive
- end-exclusive

Example:

```text
1 PM to 3 PM
```

means:

```json
[13, 14]
```

not `[13, 14, 15]`.

All `hours` arrays inside a structured directive must contain:

- unique integers,
- from 0 through 23,
- sorted ascending.

The Gemini layer should understand natural-language variants such as:
- `1 PM to 3 PM`
- `13:00 until 15:00`
- `one until three`
- equivalent paraphrases used in hidden cases.

Do not implement production interpretation as hard-coded phrase matching.

---

# 8. DIRECTIVE INTERPRETATION RESPONSE

Return exactly one interpretation entry for every input note.

Maintain:

```text
note_index = 0, 1, ... N-1
```

with no missing, duplicate, or reordered mappings.

Each interpretation entry must contain:

```text
note_index
applies
directive_type
structured_adjustment
explanation
```

The free-text `explanation` need not match public samples byte-for-byte.

Production behavior must be based on semantic interpretation, not public-case text matching.

---

# 9. GEMINI INTERPRETER

The language model is mandatory in the operator-note interpretation path.

Using Gemini only for `plan_summary`, documentation, or cosmetic text is not compliant.

## 9.1 Design goal

Use as few Gemini calls per valid request as practical.

Prefer one structured-output call for all 1–3 operator notes if Gemini's current SDK/schema support makes this reliable.

The output should contain exactly one interpretation entry per note.

Use a strict response schema if the current Gemini SDK supports it.

The Gemini prompt should contain:
- the six allowed directive types,
- exact structured-adjustment shapes,
- `applies` semantics,
- time-window convention,
- solar factor convention,
- explicit prohibition against inventing demand, tariff, battery parameters, or new directive types,
- instruction to classify unrelated notes as `no_op`.

Do not ask Gemini to solve the mathematical optimization.

## 9.2 Environment variables

At minimum design for:

```text
GEMINI_API_KEY
GEMINI_MODEL
GEMINI_FALLBACK_MODEL
GEMINI_TIMEOUT_SECONDS
GEMINI_MAX_RETRIES
```

Do not commit secret values.

Provide `.env.example` with names and safe placeholders.

Model names must be configurable rather than deeply hard-coded throughout the codebase.

During implementation choose a currently available low-latency Gemini model that supports the required structured output. Document the chosen default model.

---

# 10. LLM RETRY / FALLBACK HANDLING

This is required.

Create a bounded retry/fallback strategy that preserves the official latency limits.

The production interpreter should distinguish:

1. transient provider/network failure,
2. rate limit,
3. timeout,
4. malformed structured model output,
5. syntactically valid but guardrail-invalid model output.

Recommended strategy to validate during Phase A:

```text
Primary Gemini call
    ↓
if transient failure:
    bounded retry with short backoff
    ↓
if structured output invalid:
    one repair/retry call that includes validation errors
    ↓
if still unavailable/invalid and fallback model configured:
    fallback Gemini model
    ↓
if still invalid:
    controlled safe server error
```

Important:

- Do not silently turn failed interpretation into `no_op`.
- Do not replace the required LLM with a deterministic keyword parser.
- Do not invent a directive to keep the API alive.
- Do not retry so aggressively that the endpoint exceeds the official timeout.
- Do not leak raw model prompts containing secrets or credentials.
- Log safe diagnostic categories, not secret material.

The fallback must still be a language-capable Gemini model.

---

# 11. DETERMINISTIC LLM GUARDRAILS

Treat model output as untrusted data until deterministic validation succeeds.

Validate at least:

## Allowed type

`directive_type` must be one of:

```text
solar_reduction
minimum_battery_reserve
no_charge_window
no_discharge_window
max_grid_window
no_op
```

## Note mapping

- Every input note appears exactly once.
- `note_index` maps to a real note.
- Entries are returned in exact index order.

## `applies`

- `no_op`:
  - `applies = false`
  - `structured_adjustment = null`

- every non-`no_op`:
  - `applies = true`
  - correct adjustment object must be present

## Hours

- unique
- integers
- 0–23
- sorted ascending

## `solar_reduction`

- `factor` finite
- `0 <= factor <= 1`

## `minimum_battery_reserve`

- reserve finite
- non-negative
- not above battery capacity

## `max_grid_window`

- finite
- non-negative

## No invention

The interpretation must not modify base demand, tariff, battery parameters, or unsupported fields unless explicitly allowed by a published directive.

If model output fails guardrails:
- retry/repair within the retry budget,
- otherwise fail safely.

Never silently accept invalid LLM output.

---

# 12. ENERGY MODEL

The optimizer must obey the official GridWise rules.

For every hour:

## 12.1 Battery state

If charging:

```text
E_after = E_before + battery_kwh
```

If discharging:

```text
E_after = E_before - battery_kwh
```

If idle:

```text
E_after = E_before
battery_kwh = 0
```

## 12.2 Battery bounds

```text
active_minimum_energy_kwh <= E_after <= capacity_kwh
```

where active minimum includes any applicable reserve directive.

## 12.3 Charge/discharge rate limits

Charging:

```text
battery_kwh <= max_charge_kwh_per_hour
```

Discharging:

```text
battery_kwh <= max_discharge_kwh_per_hour
```

## 12.4 Solar

```text
0 <= solar_used_kwh <= effective_solar_kwh
```

Unused solar may be curtailed. Grid export is not part of the challenge.

## 12.5 Energy balance

Every hour:

```text
grid_kwh
+ solar_used_kwh
+ battery_discharge_kwh
=
demand_kwh
+ battery_charge_kwh
```

## 12.6 End-of-day neutrality

At the end of hour 23:

```text
battery_energy_after_kwh = initial_energy_kwh
```

This is mandatory.

---

# 13. PREFERRED LINEAR-PROGRAM FORMULATION

During Phase A verify this against the official documents.

A simple continuous formulation can use a signed battery-flow variable:

```text
b[h] > 0  => charging
b[h] < 0  => discharging
b[h] = 0  => idle
```

Suggested variables:

```text
grid[h] >= 0
solar_used[h] >= 0
battery_flow[h]
energy_after[h]
```

Base bounds:

```text
-max_discharge_kwh_per_hour <= battery_flow[h] <= max_charge_kwh_per_hour
```

Energy balance:

```text
grid[h] + solar_used[h] = demand[h] + battery_flow[h]
```

because positive `battery_flow` consumes energy for charging, while negative flow supplies energy through discharge.

Battery transition:

```text
energy_after[h] = energy_before[h] + battery_flow[h]
```

with:

```text
energy_before[0] = initial_energy_kwh
energy_before[h] = energy_after[h-1]
```

Solar:

```text
0 <= solar_used[h] <= effective_solar[h]
```

End-of-day:

```text
energy_after[23] = initial_energy_kwh
```

Directive effects can modify bounds.

### No charge

```text
upper_bound(battery_flow[h]) = 0
```

### No discharge

```text
lower_bound(battery_flow[h]) = 0
```

### Reserve

```text
energy_after[h] >= active reserve
```

### Grid cap

```text
grid[h] <= active max_grid_kwh
```

### Solar reduction

Change effective solar before optimization.

Objective:

```text
minimize Σ grid[h] * tariff[h]
```

This formulation avoids simultaneous charge/discharge variables and therefore avoids needing binary action variables.

After solving, derive:

```text
battery_action =
    "charge"    if battery_flow > tolerance
    "discharge" if battery_flow < -tolerance
    "idle"      otherwise

battery_kwh = abs(battery_flow)
```

Normalize values close to zero to exact zero before serialization.

If the official documents define any behavior that conflicts with this formulation, follow the documents instead.

---

# 14. DIRECTIVE-COMBINATION SEMANTICS

Do not invent unpublished rules.

During Phase A inspect the official documents and public samples for:
- overlapping directives,
- multiple directives of the same type affecting the same hour,
- potentially interacting reserves/caps/reductions.

Use explicitly published combination behavior where available.

If same-type overlap semantics are not defined by the official documents, call that out in the Phase A plan as an ambiguity.

Do not silently decide whether multiple solar-reduction factors multiply, whether the minimum factor wins, or any similar unspecified behavior.

Propose the safest deterministic interpretation, explain it, and wait for plan approval.

---

# 15. OPTIMIZATION OBJECTIVE

After applying all valid directives:

```text
total_cost_bdt = Σ(grid_kwh[h] * tariff_bdt_per_kwh[h])
for h = 0..23
```

Correctness comes first.

A low-cost schedule that violates an operator directive, energy balance, battery constraints, effective solar, rate limits, or final battery neutrality is invalid.

Do not sacrifice validity for lower cost.

---

# 16. SUCCESS RESPONSE CONTRACT

Top-level fields:

```text
scenario_id
directive_interpretation
hourly_plan
total_grid_kwh
total_cost_bdt
peak_grid_kwh
plan_summary
```

`scenario_id` must echo the request.

## `directive_interpretation`

One entry per input note.

## `hourly_plan`

Exactly 24 unique entries, hours 0–23.

Each entry:

```text
hour
grid_kwh
solar_used_kwh
battery_action
battery_kwh
battery_energy_after_kwh
```

Allowed actions:

```text
charge
discharge
idle
```

All reported numeric energy values must be finite and non-negative where required.

For `idle`:

```text
battery_kwh = 0
```

## Totals

Recalculate from the final plan:

```text
total_grid_kwh = sum(grid_kwh)
total_cost_bdt = sum(grid_kwh * tariff)
peak_grid_kwh = max(grid_kwh)
```

Do not trust optimizer-side cached totals without replaying the final schedule.

`plan_summary` may be deterministic. It does not need another LLM call.

---

# 17. INDEPENDENT SCHEDULE VALIDATOR / REPLAYER

This is mandatory for this implementation.

The final schedule validator must be a separate deterministic component from the optimizer.

It should not simply trust optimization solver status.

Given the original request, validated directives, and returned hourly plan, it must independently replay all 24 hours and verify:

1. exactly 24 unique hours 0–23,
2. non-negative grid energy,
3. solar usage within effective solar,
4. battery action is valid,
5. idle implies `battery_kwh = 0`,
6. battery state transition is mathematically correct,
7. capacity bound,
8. base minimum battery reserve,
9. directive-specific minimum reserve,
10. charge-rate limit,
11. discharge-rate limit,
12. no-charge windows,
13. no-discharge windows,
14. grid caps,
15. hourly energy balance,
16. demand fully served,
17. end-of-day battery energy equals initial energy,
18. recalculated total grid,
19. recalculated total cost,
20. recalculated peak grid.

Use official floating-point tolerance:

```text
0.01 kWh
0.01 BDT
```

unless a stricter official judge package is present.

Prefer tighter internal numerical tolerances and round/normalize only for serialized output.

If the optimizer returns a plan that fails the independent validator, treat it as an internal error and do not return a false-success response.

---

# 18. ERROR HANDLING

Implement a consistent JSON error format without secrets or stack traces.

Recommended HTTP behavior:

## 400

- malformed JSON
- structurally invalid request

FastAPI's default validation behavior may use 422; customize where necessary to align with the official contract.

## 422

Optional for well-formed but semantically invalid requests.

## 500

Controlled internal error such as:
- unrecoverable Gemini failure,
- optimizer internal failure,
- failed final replay,
- unexpected internal condition.

Do not expose API keys, tokens, `.env` contents, raw stack traces, or sensitive request headers.

---

# 19. PERFORMANCE

Official limits matter.

Target:

```text
GET /health ready within 60 seconds of service start
POST /optimize-energy hard limit: 30 seconds
p95 <= 5 seconds for full latency points
```

Design for p95 below 5 seconds if practical.

Performance strategy should include:
- one Gemini request for all notes where reliable,
- short bounded retry policy,
- fast deterministic validation,
- tiny 24-hour LP,
- no unnecessary database,
- no frontend dependency in the judge path,
- no provider call in `/health`.

Do not add infrastructure that creates avoidable latency.

---

# 20. PUBLIC SAMPLE TEST RUNNER

Create a local runner for:

```text
BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json
```

The file currently contains 10 worked cases.

Do not hard-code production logic around sample IDs, note wording, sample numeric values, or expected schedules.

The test runner itself may use the expected outputs for validation.

Suggested command:

```bash
python scripts/run_public_samples.py --base-url http://localhost:8000
```

The runner must:

1. load every case dynamically,
2. POST `case.input` to `/optimize-energy`,
3. verify HTTP success,
4. compare `directive_interpretation` semantically against the public expected interpretation,
5. ignore byte-for-byte `explanation` wording,
6. run the independent schedule validator,
7. verify all GridWise rules,
8. verify directive application,
9. recalculate totals,
10. compare optimized cost against the public optimal reference within official tolerance,
11. accept equivalent optimal schedules,
12. print a clear per-case PASS/FAIL report,
13. print a final summary,
14. exit non-zero on failure.

If exact public optimal cost comparison reveals multiple equivalent schedules, compare recalculated cost rather than action-sequence equality.

---

# 21. TEST STRATEGY

Create both deterministic and integration tests.

## 21.1 Deterministic unit tests

At minimum cover:

- request schema
- exactly 24 unique hours
- invalid hour ranges
- unsupported directive type
- `no_op` semantics
- non-`no_op` applies semantics
- sorted/unique directive hours
- solar factor bounds
- 80% reduction → factor 0.2 behavior
- reserve validation
- grid cap validation
- time-window conversion logic where deterministic normalization exists
- each directive's optimizer effect
- energy balance
- battery transitions
- rate limits
- capacity bounds
- minimum reserve
- final neutrality
- totals recalculation
- schedule validator failure detection

## 21.2 Optimizer tests

Use synthetic deterministic cases where the mathematically obvious optimum is known.

Test:
- cheap-hour charging / expensive-hour discharging
- no-charge blocking
- no-discharge blocking
- reserve constraints
- grid caps
- reduced solar
- final battery neutrality

## 21.3 API tests

Test:
- `/health`
- valid request
- malformed JSON
- missing fields
- incorrect hour count
- invalid numeric values
- safe LLM failure
- safe optimizer failure
- no leaked secrets

## 21.4 Gemini integration tests

Keep real-provider tests separable from normal unit tests.

For example:

```text
pytest -m "not integration"
pytest -m integration
```

Do not require a live Gemini API key for ordinary deterministic unit tests.

## 21.5 Public samples

Run all public cases against the real local service using Gemini before submission.

---

# 22. FRONTEND — VERCEL

The frontend is a demonstration tool, not part of the judge-critical path.

Do not start it until the backend acceptance tests pass.

Build a lightweight Vercel-deployable frontend.

Preferred:
- React
- TypeScript
- Vite

unless the planning phase finds a compelling reason to use Next.js.

Minimum useful UI:

1. backend status indicator using `/health`,
2. JSON scenario input textarea/editor,
3. optional public-sample selector for local/demo use,
4. Submit / Optimize button,
5. directive interpretation display,
6. totals: total grid kWh, total cost BDT, peak grid kWh,
7. 24-hour plan table,
8. readable error display.

Optional only if trivial:
- simple charts.

Do not implement authentication, user accounts, database, admin panel, complex animation, or unnecessary state-management frameworks.

Environment variable:

```text
VITE_API_BASE_URL
```

Configure backend CORS using environment-based allowed origins.

Allow localhost development and the deployed Vercel origin.

---

# 23. RENDER BACKEND DEPLOYMENT

Prepare the FastAPI backend for Render.

Use a production command equivalent to:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Exact module path may differ based on the approved structure.

Provide:
- Render build/start instructions,
- required environment-variable names,
- `/health` health-check path,
- CORS origin configuration,
- Gemini secret configuration,
- dependency installation instructions.

If useful, provide `render.yaml`, but do not create unnecessary platform complexity.

Do not put secret values in Render config committed to Git.

---

# 24. DOCKER FALLBACK

A tested Docker fallback is required.

Create a production-ready backend `Dockerfile`.

Requirements:

- binds to `0.0.0.0`,
- exposes the documented service port,
- starts FastAPI,
- works with environment variables,
- contains no baked-in API key,
- can be pulled/run without editing code.

Document commands such as:

```bash
docker build -t gridwise-api .
docker run --rm -p 8000:8000 \
  -e GEMINI_API_KEY=... \
  -e GEMINI_MODEL=... \
  gridwise-api
```

If the Docker runtime uses a configurable `PORT`, support that safely.

Add `.dockerignore`.

Before finalizing:
- build image locally,
- run it,
- wait for `/health`,
- run at least one public sample against the container.

For final submission, document how to tag and push to Docker Hub, GHCR, or equivalent. Do not fabricate a registry URL before the team actually pushes it.

---

# 25. SECURITY

Mandatory:

- no committed API keys,
- no committed `.env`,
- no passwords/tokens in source,
- no secrets in frontend,
- no secret values in README,
- no raw stack traces in API responses,
- no API-key logging,
- no baked-in Docker secrets.

Create:

```text
.env.example
.gitignore
.dockerignore
```

Frontend code must never contain the Gemini API key.

Gemini calls happen only from the backend.

---

# 26. REPOSITORY POLICY

Verify the official repository rules from the Participant Guide.

The intended policy is:

- new repository created after question reveal,
- private during the event,
- public after the submission deadline for evaluation.

Do not change repository visibility or remote configuration automatically unless I explicitly ask.

During Phase A:
- inspect current Git status/remotes,
- identify whether the current workspace appears compliant,
- mention any action I need to perform manually.

Do not delete or overwrite unrelated repository history.

---

# 27. DOCUMENTATION

Create an excellent self-contained `README.md`.

It must include:

1. project overview,
2. challenge summary,
3. architecture,
4. LLM → guardrail → optimizer → validator flow,
5. source setup,
6. Python version,
7. dependencies,
8. required environment-variable names,
9. Gemini provider/model configuration,
10. LLM role,
11. deterministic guardrails,
12. optimizer/solver,
13. exact local run command,
14. `/health` curl example,
15. `/optimize-energy` curl example,
16. public-sample runner command,
17. testing commands,
18. Docker build/run,
19. Render deployment,
20. Vercel deployment,
21. known limitations,
22. security/secret guidance,
23. external libraries/tools used and credits.

Do not include real secret values.

Also create, after implementation:

```text
docs/architecture.md
docs/deployment.md
docs/video_script.md
```

`docs/video_script.md` should fit a maximum 3-minute explanation and cover the problem, architecture, Gemini interpretation, deterministic guardrails, optimizer, independent validator, and how to run/test.

The video is tie-break material, so do not prioritize it above working backend behavior.

---

# 28. SUGGESTED PROJECT STRUCTURE

During Phase A propose the final structure before creating it.

A reasonable target is:

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── models.py
│   │   │   └── errors.py
│   │   ├── llm/
│   │   │   ├── interpreter.py
│   │   │   ├── prompts.py
│   │   │   └── schemas.py
│   │   ├── domain/
│   │   │   ├── directives.py
│   │   │   └── energy.py
│   │   ├── optimization/
│   │   │   └── optimizer.py
│   │   ├── validation/
│   │   │   ├── directive_validator.py
│   │   │   └── schedule_validator.py
│   │   └── services/
│   │       └── optimization_service.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── ...
├── scripts/
│   └── run_public_samples.py
├── tests/
│   └── fixtures/
├── docs/
│   ├── architecture.md
│   ├── deployment.md
│   └── video_script.md
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
└── README.md
```

This is a suggestion, not a mandatory structure.

Keep the codebase small and legible. Do not create unnecessary layers just to imitate enterprise architecture.

---

# 29. PUBLIC SAMPLE COVERAGE

The public sample pack contains scenarios covering combinations such as:

- solar reduction + distractor,
- battery charging maintenance,
- reserve as a percentage,
- no-discharge window,
- grid import cap,
- multiple notes + distractor,
- reserve + grid cap,
- separate charging/discharging outages,
- reduction wording normalization,
- multi-constraint evening operation.

Do not hard-code these labels or phrases into production code.

Use them only as testing coverage.

---

# 30. HIDDEN-TEST MINDSET

Assume hidden tests will vary:

- note wording,
- paraphrases,
- percentages,
- whole-hour expressions,
- demand,
- solar,
- tariff,
- battery state,
- reserve/rate limits,
- directive combinations.

Hidden notes still map to one supported directive type or `no_op`.

Production code must not:
- recognize sample IDs,
- inspect expected outputs,
- special-case known public numeric values,
- use phrase dictionaries as the sole interpreter.

The goal is genuine semantic generalization through Gemini plus deterministic guardrails.

---

# 31. FLOATING-POINT POLICY

Official comparison tolerance:

```text
absolute 0.01 kWh
absolute 0.01 BDT
```

unless a stricter judge package exists.

Internally:
- retain higher precision,
- use small solver/validation tolerances,
- normalize near-zero values,
- avoid noisy values such as `-0.0`,
- never return materially negative grid, solar, or battery magnitude values.

Do not round so aggressively that constraints become invalid.

---

# 32. OBSERVABILITY

Use simple structured logging.

Log:
- request/scenario ID,
- timing by pipeline stage,
- Gemini attempt number,
- safe provider error category,
- optimizer status,
- validation pass/fail category,
- total request latency.

Do not log:
- secrets,
- API keys,
- authorization headers,
- unnecessary full prompts,
- secret-bearing environment variables.

Keep logs useful for debugging Render failures.

---

# 33. NO DATABASE

Do not add a database.

The judge sends self-contained scenarios.

The service should be stateless.

Caching is optional and only acceptable if it cannot cause incorrect cross-request results, does not violate semantics, and does not complicate the project.

Given the short hackathon, prefer no cache unless measured need exists.

---

# 34. PLAN_SUMMARY

Do not spend another Gemini call generating `plan_summary`.

Generate a short deterministic summary from active directive types, use of solar, battery shifting, and cost minimization.

Example style:

```text
Applied the operator constraints, used available solar within the allowed limits, shifted battery energy across tariff periods, and restored the battery to its initial level by the end of hour 23.
```

This text is explanatory only. It must never be used as the source of truth.

---

# 35. FRONTEND/BACKEND DECOUPLING

Judge-critical endpoint behavior must work even if the frontend is down, Vercel is down, or browser UI is never used.

The Render API is the submission-critical service.

Frontend must communicate through the documented API only.

---

# 36. BUILD ORDER AFTER APPROVAL

Once Phase A is approved, use this implementation order.

## Milestone 1 — contracts

- project skeleton
- Pydantic models
- `/health`
- request validation
- response models
- error handling

Acceptance: schema tests pass.

## Milestone 2 — directives

- directive enums/types
- Gemini schema/prompt
- deterministic directive validator
- mocked interpreter tests

Acceptance: all directive guardrail tests pass.

## Milestone 3 — optimizer

- effective solar
- directive constraint compilation
- 24-hour LP
- schedule reconstruction
- totals

Acceptance: synthetic optimizer tests pass.

## Milestone 4 — independent validator

- complete replay engine
- totals verification
- explicit diagnostic errors

Acceptance: validator catches intentionally corrupted plans.

## Milestone 5 — service pipeline

Wire:

```text
request → Gemini → guardrails → optimizer → replay → response
```

Acceptance: local deterministic E2E tests pass.

## Milestone 6 — Gemini reliability

- real Gemini integration
- retry/repair
- fallback model
- timeout handling

Acceptance:
- real note interpretations work,
- failure paths are controlled.

## Milestone 7 — public samples

Run all provided public cases.

Acceptance:
- every public case passes interpretation checks,
- every schedule validates,
- recalculated totals match,
- cost is equivalent to public optimum within tolerance.

If any public case fails:
- diagnose root cause,
- fix the general rule,
- rerun all cases.

Do not special-case the failing sample.

## Milestone 8 — Docker

- build
- run
- health
- public-sample smoke test

## Milestone 9 — Render readiness

- production command
- env documentation
- health config
- CORS

Deployment may require my login/credentials; stop only at that authentication boundary if necessary.

## Milestone 10 — frontend

Implement minimal Vercel UI only after backend is green.

## Milestone 11 — documentation

Complete README and docs.

## Milestone 12 — final audit

Run the complete acceptance checklist below.

---

# 37. REQUIRED COMMANDS

Provide simple commands for development.

Aim for commands similar to:

```bash
# install
pip install -r backend/requirements.txt

# run backend
uvicorn backend.app.main:app --reload --port 8000

# unit tests
pytest

# real Gemini integration tests
pytest -m integration

# sample runner
python scripts/run_public_samples.py --base-url http://localhost:8000

# frontend
cd frontend
npm install
npm run dev

# Docker
docker build -t gridwise-api .
docker run --rm -p 8000:8000 --env-file .env gridwise-api
```

Adjust exact commands to the approved structure.

README commands must be copy-pasteable from a clean environment.

---

# 38. ACCEPTANCE CHECKLIST

Do not declare the project complete until all applicable items pass.

## API

- [ ] `GET /health` is exact and returns `{"status":"ok"}`.
- [ ] `POST /optimize-energy` accepts the exact schema.
- [ ] response uses the exact required top-level fields.
- [ ] scenario ID is echoed.
- [ ] all responses are JSON.

## LLM

- [ ] Gemini is genuinely used for operator-note interpretation.
- [ ] exactly one interpretation per note.
- [ ] interpretations are in note-index order.
- [ ] `no_op` semantics are exact.
- [ ] non-`no_op` semantics are exact.
- [ ] hidden-style paraphrases are handled semantically.
- [ ] invalid model output cannot silently pass.
- [ ] retry and fallback are bounded.
- [ ] provider failures are controlled.

## Guardrails

- [ ] allowed directive types only.
- [ ] hours unique/sorted/0–23.
- [ ] solar factor valid.
- [ ] reserve valid.
- [ ] grid cap valid.
- [ ] no invented fields/constraints.

## Optimization

- [ ] 24-hour schedule.
- [ ] all demand served.
- [ ] energy balance every hour.
- [ ] effective solar respected.
- [ ] battery transitions correct.
- [ ] capacity respected.
- [ ] base minimum respected.
- [ ] charge rate respected.
- [ ] discharge rate respected.
- [ ] no-charge windows respected.
- [ ] no-discharge windows respected.
- [ ] reserve directives respected.
- [ ] grid caps respected.
- [ ] final battery equals initial battery.
- [ ] objective minimizes grid electricity cost.

## Final replay

- [ ] validator independently verifies every constraint.
- [ ] total grid recalculated.
- [ ] total cost recalculated.
- [ ] peak grid recalculated.
- [ ] invalid optimizer output cannot escape as HTTP 200.

## Public cases

- [ ] all 10 current public cases execute.
- [ ] all interpretations match expected semantics.
- [ ] all schedules independently validate.
- [ ] all costs are equivalent to the public optimum within official tolerance.
- [ ] no production special-casing exists.

## Reliability

- [ ] normal valid requests do not crash.
- [ ] malformed JSON is controlled.
- [ ] provider failure is controlled.
- [ ] repeated requests remain stable.
- [ ] request timeout budget is respected.
- [ ] target p95 is considered and measured locally.

## Security

- [ ] no API key committed.
- [ ] `.env` ignored.
- [ ] safe `.env.example`.
- [ ] no frontend Gemini key.
- [ ] no secret logs.
- [ ] no raw stack traces to clients.
- [ ] Docker contains no secrets.

## Docker

- [ ] image builds.
- [ ] image starts.
- [ ] binds `0.0.0.0`.
- [ ] `/health` succeeds.
- [ ] at least one sample request succeeds against container.
- [ ] README contains pull/run instructions.

## Render

- [ ] correct start command.
- [ ] environment variables documented.
- [ ] `/health` configured.
- [ ] public endpoint can be tested externally once deployed.

## Frontend

- [ ] deployable to Vercel.
- [ ] API base URL configurable.
- [ ] can submit scenario.
- [ ] displays directive interpretation.
- [ ] displays totals.
- [ ] displays 24-hour plan.
- [ ] errors are readable.

## Documentation

- [ ] README self-contained.
- [ ] clean-environment setup documented.
- [ ] model/provider documented.
- [ ] guardrails documented.
- [ ] optimizer documented.
- [ ] tests documented.
- [ ] Docker documented.
- [ ] Render documented.
- [ ] Vercel documented.
- [ ] limitations documented.
- [ ] external tools/dependencies credited.
- [ ] 3-minute video script prepared.

---

# 39. FINAL AUDIT BEHAVIOR

After implementation, do not merely say "done."

Perform an audit against:
- the Problem Statement,
- the Participant Guide,
- every public sample case,
- this acceptance checklist.

Produce a final report with:

```text
PASS
FAIL
BLOCKED
NOT TESTED
```

for each major area.

For every failure:
- explain the root cause,
- fix it when possible,
- rerun the affected tests,
- rerun all public cases after any optimizer/directive change.

Do not hide failing tests.

Do not mark something as deployed unless it has actually been deployed and externally verified.

Do not fabricate Render URL, Vercel URL, Docker registry URL, GitHub URL, credentials, or external deployment success.

Clearly distinguish:
- implemented,
- locally verified,
- deployed,
- externally verified.

---

# 40. HACKATHON-SPECIFIC NON-GOALS

Do not waste time on:

- authentication,
- database,
- user accounts,
- persistent job queues,
- microservices,
- Kubernetes,
- complex UI,
- elaborate charts,
- custom ML training,
- fine-tuning,
- blockchain,
- unrelated analytics,
- non-required directive types,
- hard-coded public-case recognition.

Keep the system small, deterministic around the LLM, and judge-friendly.

---

# 41. PLANNING RESPONSE FORMAT

For Phase A, respond using these exact sections:

## 1. Repository / Ponytail findings

State what project instructions actually exist.

## 2. Proposed architecture

Show the full end-to-end request flow.

## 3. Proposed file structure

Show exact directories/files.

## 4. API contract implementation

Explain FastAPI/Pydantic structure and error handling.

## 5. Gemini interpreter design

Explain:
- structured output,
- prompt strategy,
- model configuration,
- retry,
- repair,
- fallback,
- latency budget.

## 6. Deterministic guardrails

List every rule.

## 7. Optimization formulation

Provide the actual mathematical variables, objective, bounds, and directive mapping.

## 8. Independent schedule validator

Explain how it will replay the final plan separately from the optimizer.

## 9. Testing strategy

Cover:
- unit,
- optimizer,
- API,
- Gemini integration,
- all public sample cases.

## 10. Render / Docker / Vercel

Explain deployment approach and environment variables.

## 11. Security

Explain secret handling.

## 12. Scoring-priority implementation order

Optimize the plan for the official scoring rubric.

## 13. Ambiguities / assumptions

List anything not explicitly defined in the official documents.

## 14. Estimated implementation sequence

Give a concise milestone order.

## 15. Approval checkpoint

Finish with:

> Planning complete. I have not modified the repository. Please approve or request changes before I begin implementation.

---

# 42. FINAL OPERATING PRINCIPLES

Throughout this project:

- official documents beat assumptions,
- correctness beats cleverness,
- deterministic validation surrounds the LLM,
- no public-sample hard-coding,
- no hidden heuristics pretending to be LLM interpretation,
- no optimization result is trusted without replay,
- no secrets are committed,
- no deployment success is fabricated,
- backend scoring requirements beat frontend polish,
- fix general rules rather than special-casing examples,
- keep the system simple enough to finish under hackathon pressure.

Begin with **Phase A only**.
