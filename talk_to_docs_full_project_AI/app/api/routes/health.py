from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.metrics import API_REQUESTS

router = APIRouter()

@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Check database connection
        db.execute("SELECT 1")
        API_REQUESTS.labels(endpoint="/health", method="GET", status="success").inc()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        API_REQUESTS.labels(endpoint="/health", method="GET", status="error").inc()
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)} 