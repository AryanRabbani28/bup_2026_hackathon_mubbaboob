# Deployment Guide

This guide details how to deploy the GridWise API backend to Render, build and run the Docker fallback image, and deploy the frontend to Vercel.

## 1. Render Deployment (Backend)

The backend is built with FastAPI and is production-ready for deployment as a Render Web Service.

### Configuration on Render:
- **Environment**: Python 3
- **Root Directory**: `backend` (or repo root with command pointing to backend)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`

### Environment Variables:
Set the following in the Render dashboard:
- `GEMINI_API_KEY`: Your Google Gemini API Key.
- `GEMINI_MODEL`: `gemini-3.5-flash` (or `gemini-2.5-flash`).
- `GEMINI_FALLBACK_MODEL`: `gemini-3.5-flash-lite`.
- `GEMINI_TIMEOUT_SECONDS`: `25`
- `GEMINI_MAX_RETRIES`: `2`

*(Never commit your real `GEMINI_API_KEY` into Git!)*

---

## 2. Docker Fallback Image

A verified Dockerfile is included in `backend/Dockerfile`.

### Build Image:
```bash
cd backend
docker build -t gridwise-api:latest .
```

### Run Container:
```bash
docker run --rm -p 8000:8000 \
  -e GEMINI_API_KEY="your_api_key" \
  -e GEMINI_MODEL="gemini-3.5-flash" \
  -e GEMINI_FALLBACK_MODEL="gemini-3.5-flash-lite" \
  gridwise-api:latest
```

### Test Container:
Check health:
```bash
curl http://localhost:8000/health
```
Execute public sample test:
```bash
cd ..
python scripts/run_public_samples.py --base-url http://localhost:8000
```

---

## 3. Vercel Deployment (Frontend)

The frontend is a lightweight Vite + React + TypeScript single-page application.

### Configuration on Vercel:
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Environment Variables:
- `VITE_API_BASE_URL`: The URL of your deployed Render backend (e.g. `https://gridwise-backend.onrender.com`).
