# GridWise LLM Smart Campus Optimization

This repository contains the backend and frontend for the BUP CSE FEST 2026 Hackathon — GridWise LLM-Assisted Smart Campus Energy Optimization Challenge.

## Architecture

The service consists of a FastAPI backend and a minimal Vercel frontend. The request flow is:
1. **Request** -> **Schema Validation** (Pydantic)
2. **LLM Interpreter** -> **Gemini API** extracts structured adjustments from natural-language `operator_notes`.
3. **Deterministic Guardrails** -> Verifies the extracted directives are valid, within range, and safely mapped.
4. **Optimization** -> Mathematical 24-hour Linear Programming using `scipy.optimize.linprog(method="highs")` to minimize grid cost while respecting the directives.
5. **Independent Validator** -> Replays the generated schedule hour by hour to verify all energy bounds, balances, and operational constraints are fully respected.
6. **Response** -> Returns the interpreted directives, optimized schedule, and recalculated totals.

## Setup & Running Locally

### Prerequisites
- Python 3.11+
- Node.js (for frontend)
- A valid Google Gemini API key

### Backend

1. **Clone the repository and enter the backend directory:**
```bash
git clone <your-repo-url>
cd backend
```

2. **Set up the environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure the environment variables:**
Create a `.env` file in the `backend` directory (copy from `.env.example`):
```bash
cp .env.example .env
```
Edit `.env` to include your `GEMINI_API_KEY`.

4. **Run the server:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The API is now running at `http://localhost:8000`.

### Testing

**Deterministic Unit & Optimization Tests:**
```bash
pytest -m "not integration"
```

**Real Gemini Integration Tests:**
(Requires `GEMINI_API_KEY` in `.env`)
```bash
pytest -m integration
```

**Public Sample Test Runner:**
This script evaluates the 10 provided public samples against your local API instance.
```bash
cd ..
python scripts/run_public_samples.py --base-url http://localhost:8000
```

### Curl Examples

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Optimize Energy:**
```bash
curl -X POST "http://localhost:8000/optimize-energy" \
     -H "Content-Type: application/json" \
     -d @../BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json
# Modify the payload to send only one valid scenario.
```

## Docker

A ready-to-run `Dockerfile` is provided for the backend.

```bash
cd backend
docker build -t gridwise-api .
docker run --rm -p 8000:8000 --env-file .env gridwise-api
```

## Render Deployment

This service is ready to be deployed on Render as a Web Service.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: Make sure to set `GEMINI_API_KEY` in the Render dashboard. DO NOT commit it to Git.

## Vercel Deployment

The frontend (located in the `frontend` directory) is a standard Vite React app deployable to Vercel.
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variable**: Configure `VITE_API_BASE_URL` in Vercel to point to your deployed Render backend (e.g., `https://gridwise-api.onrender.com`).

## Security & Limitations

- **No Secrets in Source**: The `.env` file and any API keys MUST NEVER be committed to this repository. The frontend contains no sensitive keys.
- **Controlled Error Handling**: The API returns safe `500` error structures for internal crashes and provider timeouts, masking all stack traces.
- **No Database**: This system is completely stateless.
- **LLM Rate Limits**: High concurrency might hit Gemini rate limits. A short back-off and fallback retry mechanism is implemented.

## External Libraries

- **FastAPI / Pydantic / Uvicorn**: For robust HTTP endpoints and validation.
- **SciPy (`linprog`)**: For exact deterministic constraint scheduling.
- **Google Generative AI SDK**: For integration with Gemini 1.5 Flash/Pro models.
- **Pytest / HTTPX**: For extensive deterministic and network testing.
- **Vite / React**: For the lightweight interactive frontend.
