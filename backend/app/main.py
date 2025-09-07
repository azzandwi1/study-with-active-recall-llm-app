from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from app.core.settings import settings
from app.core.database import init_db, get_db
from app.core.logging_config import setup_logging
from app.core.exceptions import ActiveRecallException
from app.api.v1 import ingest, generate, quiz, review, health

# Configure logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Active Recall Backend API")
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Active Recall Backend API")


# Create FastAPI app
app = FastAPI(
    title="Active Recall Backend API",
    description="Backend API for Active Recall learning application with AI-powered flashcard generation and spaced repetition",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get API key from headers
def get_api_key(request: Request) -> str:
    """Extract and validate API key from request headers"""
    api_key = request.headers.get("X-User-Gemini-Key")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="X-User-Gemini-Key header is required for all LLM operations"
        )
    
    return api_key


# Custom exception handler for ActiveRecallException
@app.exception_handler(ActiveRecallException)
async def active_recall_exception_handler(request: Request, exc: ActiveRecallException):
    """Handle custom Active Recall exceptions"""
    logger.warning(f"ActiveRecallException: {exc}")
    
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "type": exc.__class__.__name__
        }
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if getattr(settings, 'debug', False) else "An unexpected error occurred"
        }
    )


# Include API routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(generate.router, prefix="/api/v1", tags=["generate"])
app.include_router(quiz.router, prefix="/api/v1", tags=["quiz"])
app.include_router(review.router, prefix="/api/v1", tags=["review"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Active Recall Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint (also available via router)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "active-recall-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
