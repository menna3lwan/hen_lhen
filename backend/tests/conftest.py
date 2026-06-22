"""Test fixtures — async SQLite in-memory database, test client, seed data."""

import uuid
import asyncio
from datetime import date, time, datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import JSON, event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, INET

from app.db.base import Base
from app.db.session import get_db
from app.core.security import create_access_token, hash_password

# ── SQLite compatibility: remap Postgres-only types ──

@event.listens_for(Base.metadata, "before_create")
def _remap_pg_types(target, connection, **kw):
    """Replace JSONB/INET with SQLite-friendly types for testing."""
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            for col in table.columns:
                if isinstance(col.type, JSONB):
                    col.type = JSON()
                elif isinstance(col.type, INET):
                    from sqlalchemy import String
                    col.type = String(45)
from app.models.user import User, Patient, Doctor, UserRole, VerificationStatus
from app.models.specialty import Specialty
from app.models.appointment import Appointment, AppointmentType, AppointmentStatus
from app.models.payment import Payment, PaymentStatus
from app.models.chat import ChatRoom, ChatStatus
from app.models.notification import Notification, NotificationType
from app.models.device import Device, DevicePlatform
from app.main import create_app

# ── Async engine (SQLite in-memory) ──

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Fixtures ──

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Provide a test DB session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def app(db):
    """Create test FastAPI app with DB override."""
    app = create_app()

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest_asyncio.fixture
async def client(app):
    """Async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Seed data ──

@pytest_asyncio.fixture
async def specialty(db):
    spec = Specialty(
        id=uuid.uuid4(),
        name_ar="طب عام",
        name_en="General Medicine",
        icon="general",
        color="#4CAF50",
    )
    db.add(spec)
    await db.commit()
    return spec


@pytest_asyncio.fixture
async def patient_user(db):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        email="patient@test.com",
        phone="01000000001",
        password_hash=hash_password("test123456"),
        role=UserRole.PATIENT,
        name="مريضة تست",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    patient = Patient(id=uid, governorate="القاهرة")
    db.add(patient)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def doctor_user(db, specialty):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        email="doctor@test.com",
        phone="01000000002",
        password_hash=hash_password("test123456"),
        role=UserRole.DOCTOR,
        name="د. تست",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    doctor = Doctor(
        id=uid,
        specialty_id=specialty.id,
        license_number="DOC-TEST-001",
        experience_years=5,
        consultation_fee=200.00,
        verification_status=VerificationStatus.APPROVED,
    )
    db.add(doctor)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def admin_user(db):
    uid = uuid.uuid4()
    user = User(
        id=uid,
        email="admin@test.com",
        phone="01000000003",
        password_hash=hash_password("test123456"),
        role=UserRole.ADMIN,
        name="مسؤول تست",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def patient_token(patient_user):
    return create_access_token(str(patient_user.id), "patient")


@pytest_asyncio.fixture
async def doctor_token(doctor_user):
    return create_access_token(str(doctor_user.id), "doctor")


@pytest_asyncio.fixture
async def admin_token(admin_user):
    return create_access_token(str(admin_user.id), "admin")


@pytest_asyncio.fixture
async def pending_appointment(db, patient_user, doctor_user):
    """Create a PENDING appointment for payment tests."""
    appt = Appointment(
        id=uuid.uuid4(),
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        date=date(2026, 7, 15),
        time=time(10, 0),
        type=AppointmentType.ONLINE,
        status=AppointmentStatus.PENDING,
        amount=200.00,
        discount_amount=0.00,
    )
    db.add(appt)
    await db.commit()
    return appt


@pytest_asyncio.fixture
async def confirmed_appointment(db, patient_user, doctor_user):
    """Create a CONFIRMED appointment for chat tests."""
    appt = Appointment(
        id=uuid.uuid4(),
        patient_id=patient_user.id,
        doctor_id=doctor_user.id,
        date=date(2026, 7, 16),
        time=time(14, 0),
        type=AppointmentType.ONLINE,
        status=AppointmentStatus.CONFIRMED,
        amount=200.00,
        discount_amount=0.00,
    )
    db.add(appt)
    await db.commit()
    return appt
