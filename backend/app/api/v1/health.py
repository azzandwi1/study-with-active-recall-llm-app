from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import Collection
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "active-recall-backend",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check including database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        # Test basic model access
        collection_count = db.query(Collection).count()
        
        return {
            "status": "ready",
            "database": "connected",
            "collections": collection_count
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/live")
async def liveness_check():
    """Liveness check for container orchestration"""
    return {
        "status": "alive",
        "timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp
    }
