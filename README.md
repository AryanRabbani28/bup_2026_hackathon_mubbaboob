# GridWise — LLM-Assisted Smart Campus Energy Optimization

Production submission for the **BUP CSE FEST 2026 Hackathon** — *GridWise LLM-Assisted Smart Campus Energy Optimization Challenge*.

---

## 🌐 Live Production Endpoints

| Component | URL | Description |
| :--- | :--- | :--- |
| **Backend API** | `https://gridwise-backend-ds0n.onrender.com` | Deployed FastAPI service on Render |
| **Health Check** | `https://gridwise-backend-ds0n.onrender.com/health` | Service liveness endpoint |
| **Interactive Docs (Swagger)** | `https://gridwise-backend-ds0n.onrender.com/docs` | In-browser API testing UI |
| **Optimization Endpoint** | `POST https://gridwise-backend-ds0n.onrender.com/optimize-energy` | Main competition evaluation endpoint |
| **Frontend Dashboard** | [`https://gridwise-frontend.vercel.app`](https://gridwise-frontend.vercel.app) | Single Page Application for interactive visualization |

---

## 📋 Evaluation Guide (For Judges)

The judging evaluation system tests the backend programmatically by sending HTTP `POST` requests directly to `/optimize-energy`. No browser or UI is required.

### Endpoint Specification
- **URL**: `https://gridwise-backend-ds0n.onrender.com/optimize-energy`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Payload**: Full scenario object containing `scenario_id`, `operator_notes`, `hours` (0–23), and `battery` configuration.

---

### Method 1: Automated Test Runner (Recommended)
You can evaluate your testcase file (e.g. `BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json`) directly against the live backend:

```bash
# Evaluate all sample cases against the live Render endpoint:
python scripts/run_public_samples.py --base-url https://gridwise-backend-ds0n.onrender.com
```
*Current test result on live deployment: **10 passed, 0 failed (100% match)**.*

---

### Method 2: Programmatic Python Script
Judges can evaluate custom hidden cases using standard Python (`requests` or `httpx`):

```python
import requests

payload = {
    "scenario_id": "JUDGE-CASE-01",
    "operator_notes": [
        "Facilities will wash the rooftop solar panels from noon until 2 PM. During cleaning, usable solar should be treated as roughly 25% of the forecast.",
        "The sports office moved next month's registration deadline."
    ],
    "hours": [
        {"hour": 0, "demand_kwh": 90, "solar_kwh": 0, "tariff_bdt_per_kwh": 6},
        # ... hours 1 to 23
    ],
    "battery": {
        "capacity_kwh": 300,
        "initial_energy_kwh": 110,
        "minimum_energy_kwh": 40,
        "max_charge_kwh_per_hour": 50,
        "max_discharge_kwh_per_hour": 50
    }
}

url = "https://gridwise-backend-ds0n.onrender.com/optimize-energy"
response = requests.post(url, json=payload, timeout=45)

if response.status_code == 200:
    data = response.json()
    print("Scenario ID:        ", data["scenario_id"])
    print("Total Cost (BDT):   ", data["total_cost_bdt"])
    print("Total Grid (kWh):   ", data["total_grid_kwh"])
    print("Peak Grid (kWh):    ", data["peak_grid_kwh"])
    print("Directives Decoded: ", len(data["directive_interpretation"]))
    print("Plan Summary:       ", data["plan_summary"])
else:
    print(f"Error {response.status_code}: {response.text}")
```

---

### Method 3: Command Line via `curl`
To evaluate a testcase stored in a JSON file:

```bash
curl -X POST "https://gridwise-backend-ds0n.onrender.com/optimize-energy" \
     -H "Content-Type: application/json" \
     -d @testcase.json
```

---

### Method 4: Interactive Swagger UI (Browser Testing)
Judges can also inspect schemas and execute test cases interactively in the browser without any tooling:
1. Open **[https://gridwise-backend-ds0n.onrender.com/docs](https://gridwise-backend-ds0n.onrender.com/docs)**
2. Click **`POST /optimize-energy`**
3. Click **Try it out**
4. Paste the scenario JSON into the request body and click **Execute**
5. Inspect the HTTP `200` response, formatted JSON, and headers.

---

## 🖥️ User Interaction Guide (Frontend Dashboard)

For visual inspection, exploratory testing, and stakeholder review, the frontend dashboard is live at **[https://gridwise-frontend.vercel.app](https://gridwise-frontend.vercel.app)**.

### Key Features
1. **Real-Time API Health Status**: Top-right status indicator shows `API Connected` in green when the Render backend is healthy and reachable.
2. **One-Click "Try Example"**: Automatically loads a realistic campus scenario (solar cleaning window + distractor note) into the editor.
3. **Custom JSON Input**: Paste any valid scenario JSON directly into the editor and hit **Run Optimization**.
4. **Visual Directive Interpretations**: Shows each operator note alongside the extracted directive type (`solar_reduction`, `no_op`, `minimum_battery_reserve`, etc.), status (`applies: true/false`), and natural language reasoning.
5. **Interactive 24-Hour Dispatch Chart**: Visualizes demand curves, solar generation, grid imports, and battery charging/discharging states throughout the day.
6. **Detailed Hourly Schedule Table**: Full hour-by-hour audit table showing `grid_kwh`, `solar_used_kwh`, `battery_action`, `battery_kwh`, and battery state-of-charge (`battery_energy_after_kwh`).
7. **KPI Summary Cards**: Immediate display of Total Grid Energy, Total Cost (BDT), Peak Hourly Grid Import, and Battery Neutrality verification.

---

## 🏗️ System Architecture & Workflow

The system is designed with a defense-in-depth, deterministic-first architecture:

```
[Request JSON] 
      │
      ▼
1. Pydantic Schema Validation ──▶ Rejects malformed types, missing hours, invalid bounds
      │
      ▼
2. LLM Directive Interpreter ──▶ Gemini 1.5/2.5 Flash extracts structured JSON adjustments
      │
      ▼
3. Deterministic Guardrails   ──▶ Clamps windows to [0,23], validates factors, rejects invalid enums
      │
      ▼
4. Exact LP Optimization     ──▶ SciPy linprog (HiGHS solver) solves 24h mathematical cost minimization
      │
      ▼
5. Independent Validator      ──▶ Replays schedule hour-by-hour to enforce physical balances & battery neutrality
      │
      ▼
[Response JSON (200 OK)]
```

---

## ⚙️ Local Development & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- A Google Gemini API key

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Copy example environment
cp .env.example .env
# Edit .env to set your GEMINI_API_KEY

# Run FastAPI backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
API runs locally at `http://localhost:8000`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs locally at `http://localhost:5173`.

---

## 🧪 Testing

### Deterministic Unit & Optimization Tests
```bash
pytest -m "not integration"
```

### Full Gemini Integration Tests
```bash
pytest -m integration
```

### Public Sample Verification Runner
```bash
python scripts/run_public_samples.py --base-url http://localhost:8000
```

---

## 🐳 Docker Deployment

A verified Dockerfile is included:
```bash
cd backend
docker build -t gridwise-api:latest .
docker run --rm -p 8000:8000 --env-file .env gridwise-api:latest
```

---

## 🔒 Security & Reliability

- **No Committed Secrets**: API keys are injected via environment variables (`GEMINI_API_KEY`) and are never exposed in git or client code.
- **Fail-Safe Fallbacks**: If the LLM provider experiences latency or rate limits, retries and fallback models (`gemini-3.5-flash-lite`) engage automatically.
- **Strict Energy Balances**: The LP formulation strictly enforces the physical constraint:
  $$\text{grid\_kwh} + \text{solar\_used\_kwh} + \text{battery\_discharge\_kwh} = \text{demand\_kwh} + \text{battery\_charge\_kwh}$$
  along with mandatory end-of-day battery state-of-charge neutrality ($E_{23} = E_{\text{initial}}$).
