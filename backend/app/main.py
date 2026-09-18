from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from .api.models import OptimizeRequest, OptimizeResponse
from .api.errors import validation_exception_handler, generic_exception_handler

app = FastAPI(title="GridWise Optimization API")

# Add CORS middleware to allow local and Vercel frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, we should restrict this based on VITE_API_BASE_URL or domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.get("/health")
async def health():
    return {"status": "ok"}

from .services.optimization_service import process_optimization_request

@app.post("/optimize-energy", response_model=OptimizeResponse)
async def optimize_energy(request: OptimizeRequest):
    return await process_optimization_request(request)
