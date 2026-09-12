import logging
import sys
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import core modules
from core.config import settings
from core.database import engine, Base
from core.errors import APIError, PayloadTooLargeError

# Import routers
from routers import auth, widgets, public, dashboard


# Create FastAPI application
app = FastAPI(
    title="FlyRank Widget Platform",
    description="Embeddable widget and lead-capture platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=False,  # Keep False when allow_origins is "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Request size middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Middleware to limit request body size."""
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size:
            logger.warning(f"Request size {content_length} exceeds limit {settings.max_request_size}")
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": "Request body exceeds the maximum allowed size."
                    }
                }
            )
    
    response = await call_next(request)
    return response


# Global exception handler
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle custom API errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred."
            }
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(widgets.router)
app.include_router(public.router)
app.include_router(dashboard.router)

# Mount static files with long cache for versioned assets
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "FlyRank Widget Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Static file middleware with proper headers
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    """Add appropriate cache headers for static assets."""
    response = await call_next(request)
    
    # Long-lived cache for versioned static assets
    if request.url.path.startswith("/static/"):
        if "widget.v1.js" in request.url.path:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "public, max-age=86400"
    
    return response


def create_tables():
    """Create database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


if __name__ == "__main__":
    # Create tables on startup
    create_tables()
    
    # Start the server
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )