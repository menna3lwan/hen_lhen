"""Seed database with initial data (specialties, admin user)."""

import asyncio
import uuid
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.specialty import Specialty
from app.models.user import User, UserRole
from app.core.security import hash_password


SPECIALTIES = [
    {"name_ar": "نساء وتوليد", "name_en": "Obstetrics & Gynecology", "icon": "🩺", "color": 0xFFE91E8C, "sort_order": 0},
    {"name_ar": "جلدية", "name_en": "Dermatology", "icon": "🧴", "color": 0xFF6C63FF, "sort_order": 1},
    {"name_ar": "نفسية", "name_en": "Psychiatry", "icon": "🧠", "color": 0xFF4CAF50, "sort_order": 2},
    {"name_ar": "تغذية", "name_en": "Nutrition", "icon": "🥗", "color": 0xFFFF9800, "sort_order": 3},
    {"name_ar": "أطفال", "name_en": "Pediatrics", "icon": "👶", "color": 0xFF2196F3, "sort_order": 4},
    {"name_ar": "باطنة", "name_en": "Internal Medicine", "icon": "💊", "color": 0xFF9C27B0, "sort_order": 5},
]


async def seed_specialties(session):
    """Seed specialties if table is empty."""
    result = await session.execute(select(Specialty).limit(1))
    if result.scalar_one_or_none():
        print("Specialties already seeded, skipping.")
        return

    for s in SPECIALTIES:
        session.add(Specialty(**s))
    await session.flush()
    print(f"Seeded {len(SPECIALTIES)} specialties.")


async def seed_admin(session):
    """Create default admin user if none exists."""
    result = await session.execute(
        select(User).where(User.role == UserRole.ADMIN).limit(1)
    )
    if result.scalar_one_or_none():
        print("Admin user already exists, skipping.")
        return

    admin = User(
        name="Admin",
        email="admin@henlehen.com",
        phone="01000000000",
        password_hash=hash_password("admin123456"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    session.add(admin)
    await session.flush()
    print(f"Created admin user: admin@henlehen.com / admin123456")


async def run_seed():
    """Run all seed functions."""
    async with AsyncSessionLocal() as session:
        try:
            await seed_specialties(session)
            await seed_admin(session)
            await session.commit()
            print("Seeding complete!")
        except Exception as e:
            await session.rollback()
            print(f"Seeding failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
