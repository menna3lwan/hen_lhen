"""V1 API router — aggregates all endpoint routers."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    health,
    doctors,
    patients,
    appointments,
    branches,
    reviews,
    favorites,
    notifications,
    community,
    admin,
    payments,
    chat,
    devices,
    uploads,
    medical_records,
    admin_dashboard,
    specialties,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(specialties.router)
api_router.include_router(doctors.router)
api_router.include_router(patients.router)
api_router.include_router(appointments.router)
api_router.include_router(branches.router)
api_router.include_router(reviews.router)
api_router.include_router(favorites.router)
api_router.include_router(notifications.router)
api_router.include_router(community.router)
api_router.include_router(admin.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(payments.router)
api_router.include_router(chat.router)
api_router.include_router(devices.router)
api_router.include_router(uploads.router)
api_router.include_router(medical_records.router)
