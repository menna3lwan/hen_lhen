"""Doctor service — listing, search, profile, availability."""

import uuid
from datetime import date, time, datetime, timedelta
from typing import Optional, List, Tuple

from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Doctor, UserRole, VerificationStatus
from app.models.specialty import Specialty
from app.models.branch import Branch, BranchSchedule
from app.models.appointment import Appointment, AppointmentStatus


class DoctorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_doctors(
        self,
        specialty: Optional[str] = None,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "desc",
        online: Optional[bool] = None,
        governorate: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        """List approved doctors with search/filter/sort/pagination."""

        query = (
            select(Doctor, User, Specialty)
            .join(User, Doctor.id == User.id)
            .join(Specialty, Doctor.specialty_id == Specialty.id)
            .where(
                Doctor.verification_status == VerificationStatus.APPROVED,
                User.is_active == True,
                User.deleted_at == None,
            )
        )

        # Filters
        if specialty:
            query = query.where(
                or_(
                    Specialty.name_en.ilike(f"%{specialty}%"),
                    Specialty.name_ar.ilike(f"%{specialty}%"),
                )
            )

        if search:
            query = query.where(
                or_(
                    User.name.ilike(f"%{search}%"),
                    Specialty.name_ar.ilike(f"%{search}%"),
                    Specialty.name_en.ilike(f"%{search}%"),
                )
            )

        if online is not None:
            query = query.where(Doctor.is_online == online)

        if governorate:
            # Filter by doctors who have a branch in this governorate
            branch_subq = (
                select(Branch.doctor_id)
                .where(Branch.governorate.ilike(f"%{governorate}%"), Branch.is_active == True)
                .distinct()
            )
            query = query.where(Doctor.id.in_(branch_subq))

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Sort
        sort_map = {
            "rating": Doctor.rating,
            "fee": Doctor.consultation_fee,
            "experience": Doctor.experience_years,
        }
        sort_col = sort_map.get(sort, Doctor.rating)
        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        # Pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        doctors = []
        for doctor, user, spec in rows:
            doctors.append({
                "id": user.id,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "specialty_name_ar": spec.name_ar,
                "specialty_name_en": spec.name_en,
                "consultation_fee": float(doctor.consultation_fee),
                "rating": float(doctor.rating),
                "reviews_count": doctor.reviews_count,
                "experience_years": doctor.experience_years,
                "patients_count": doctor.patients_count,
                "is_online": doctor.is_online,
                "is_verified": user.is_verified,
            })

        return doctors, total

    async def get_doctor_profile(self, doctor_id: uuid.UUID) -> Optional[dict]:
        """Get full doctor profile with branches."""
        result = await self.db.execute(
            select(Doctor, User, Specialty)
            .join(User, Doctor.id == User.id)
            .join(Specialty, Doctor.specialty_id == Specialty.id)
            .where(Doctor.id == doctor_id, User.deleted_at == None)
        )
        row = result.first()
        if not row:
            return None

        doctor, user, spec = row

        # Load branches
        branches_result = await self.db.execute(
            select(Branch)
            .where(Branch.doctor_id == doctor_id, Branch.deleted_at == None)
            .order_by(Branch.created_at)
        )
        branches = branches_result.scalars().all()

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "specialty_id": doctor.specialty_id,
            "specialty_name_ar": spec.name_ar,
            "specialty_name_en": spec.name_en,
            "license_number": doctor.license_number,
            "experience_years": doctor.experience_years,
            "bio": doctor.bio,
            "consultation_fee": float(doctor.consultation_fee),
            "rating": float(doctor.rating),
            "reviews_count": doctor.reviews_count,
            "patients_count": doctor.patients_count,
            "is_online": doctor.is_online,
            "is_verified": user.is_verified,
            "verification_status": doctor.verification_status.value,
            "branches": [
                {
                    "id": b.id,
                    "name": b.name,
                    "governorate": b.governorate,
                    "area": b.area,
                    "address": b.address,
                    "phone": b.phone,
                    "consultation_fee": float(b.consultation_fee),
                    "is_active": b.is_active,
                }
                for b in branches
            ],
        }

    async def update_doctor_profile(
        self, doctor_id: uuid.UUID, data: dict
    ) -> Optional[dict]:
        """Update doctor's profile fields."""
        user = await self.db.get(User, doctor_id)
        doctor = await self.db.get(Doctor, doctor_id)
        if not user or not doctor:
            return None

        if "name" in data and data["name"]:
            user.name = data["name"]
        if "phone" in data and data["phone"]:
            user.phone = data["phone"]
        if "bio" in data and data["bio"] is not None:
            doctor.bio = data["bio"]
        if "consultation_fee" in data and data["consultation_fee"] is not None:
            doctor.consultation_fee = data["consultation_fee"]

        await self.db.flush()
        return await self.get_doctor_profile(doctor_id)

    async def set_online_status(
        self, doctor_id: uuid.UUID, is_online: bool
    ) -> bool:
        """Toggle doctor online/offline."""
        doctor = await self.db.get(Doctor, doctor_id)
        if not doctor:
            return False
        doctor.is_online = is_online
        await self.db.flush()
        return True

    async def get_availability(
        self, doctor_id: uuid.UUID, target_date: date, branch_id: Optional[uuid.UUID] = None
    ) -> List[dict]:
        """Get available time slots for a doctor on a specific date."""
        # Determine day of week (Saturday=0 in our schema)
        # Python: Monday=0..Sunday=6; we want Saturday=0..Friday=6
        py_dow = target_date.weekday()  # Mon=0
        our_dow = (py_dow + 2) % 7  # Sat=0

        # Find schedules
        sched_query = select(BranchSchedule).join(Branch).where(
            Branch.doctor_id == doctor_id,
            Branch.is_active == True,
            Branch.deleted_at == None,
            BranchSchedule.day_of_week == our_dow,
            BranchSchedule.is_active == True,
        )
        if branch_id:
            sched_query = sched_query.where(Branch.id == branch_id)

        result = await self.db.execute(sched_query)
        schedules = result.scalars().all()

        if not schedules:
            return []

        # Get existing appointments for this date
        appt_result = await self.db.execute(
            select(Appointment.time).where(
                Appointment.doctor_id == doctor_id,
                Appointment.date == target_date,
                Appointment.status.in_([
                    AppointmentStatus.PENDING,
                    AppointmentStatus.CONFIRMED,
                ]),
            )
        )
        booked_times = {row[0] for row in appt_result.all()}

        # Generate slots from all matching schedules
        slots = []
        seen_times = set()
        for sched in schedules:
            current = datetime.combine(target_date, sched.start_time)
            end = datetime.combine(target_date, sched.end_time)
            delta = timedelta(minutes=sched.slot_duration_minutes)

            while current + delta <= end:
                t = current.time()
                time_str = t.strftime("%H:%M")
                if time_str not in seen_times:
                    seen_times.add(time_str)
                    slots.append({
                        "time": time_str,
                        "is_available": t not in booked_times,
                    })
                current += delta

        slots.sort(key=lambda s: s["time"])
        return slots
