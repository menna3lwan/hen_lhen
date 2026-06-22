"""Health check endpoints — basic and detailed."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.cache import cache
from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Basic health check — always fast."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }


@router.get("/health/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    """Detailed health check — database, cache, uptime."""
    checks = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)[:100]}

    # Redis cache
    checks["cache"] = {
        "status": "ok" if cache.is_connected else "fallback",
        "backend": "redis" if cache.is_connected else "in-memory",
    }

    # Overall
    all_ok = all(c.get("status") == "ok" for c in checks.values())

    return {
        "status": "ok" if all_ok else "degraded",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
