"""Specialties endpoints — cached list of medical specialties."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.specialty import Specialty
from app.core.cache import cache, specialties_key

router = APIRouter(prefix="/specialties", tags=["Specialties"])


@router.get("")
async def list_specialties(db: AsyncSession = Depends(get_db)):
    """List all active specialties (cached)."""
    # Try cache first
    cached = await cache.get(specialties_key())
    if cached:
        return {"data": cached, "cached": True}

    # DB fallback
    result = await db.execute(
        select(Specialty)
        .where(Specialty.is_active == True)
        .order_by(Specialty.sort_order, Specialty.name_ar)
    )
    specialties = result.scalars().all()

    data = [
        {
            "id": str(s.id),
            "name_ar": s.name_ar,
            "name_en": s.name_en,
            "icon": s.icon,
            "color": s.color,
        }
        for s in specialties
    ]

    # Cache for 1 hour
    from app.core.config import settings
    await cache.set(specialties_key(), data, ttl=settings.CACHE_TTL_SPECIALTIES)

    return {"data": data, "cached": False}
