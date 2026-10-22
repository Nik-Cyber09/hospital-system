"""
FastAPI main application entry point for Carepoint Hospital Management.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.database import connect_database, disconnect_database
from app.routes import auth, records
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("carepoint")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    logger.info("Initializing Carepoint Hospital API...")
    db = await connect_database()
    # Ensure indexes exist on startup
    from app.models import User, HospitalRecord
    user_model = User(db)
    record_model = HospitalRecord(db)
    await user_model.create_indexes()
    await record_model.create_indexes()
    logger.info("Indexes initialized successfully.")
    yield
    logger.info("Shutting down Carepoint Hospital API...")
    await disconnect_database()

# Create FastAPI app
app = FastAPI(
    title="Carepoint Hospital API",
    description="Hospital Management System API built with FastAPI and MongoDB",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers ensuring both 'error' and 'detail' are present
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = errors[0].get("msg", "Invalid request data.") if errors else "Validation error."
    loc = " -> ".join([str(x) for x in errors[0].get("loc", [])]) if errors else ""
    full_msg = f"{loc}: {msg}" if loc else msg
    return JSONResponse(
        status_code=400,
        content={"detail": full_msg, "error": full_msg},
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error": str(exc)},
    )

# Include routers
app.include_router(auth.router)
app.include_router(records.router)

# Health check endpoints
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Carepoint Hospital API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.node_env == "development",
    )
