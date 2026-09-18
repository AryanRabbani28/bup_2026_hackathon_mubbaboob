from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Union

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors securely, avoiding internal leakage,
    returning a 400 response as per contract.
    """
    safe_errors = []
    for err in exc.errors():
        safe_errors.append({
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": str(err.get("msg", "")),
            "type": str(err.get("type", ""))
        })
    return JSONResponse(
        status_code=400,
        content={"detail": "Malformed JSON or structurally invalid request.", "errors": safe_errors}
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unhandled server errors safely. Returns 500 without leaking stack traces.
    """
    # In a real system, we'd log `exc` here with a secure logger.
    return JSONResponse(
        status_code=500,
        content={"detail": "Controlled internal error."}
    )
