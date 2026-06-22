"""Appointment service — booking, management, conflict detection."""

import uuid
from datetime import date, time, datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Doctor, Patient, UserRole, VerificationStatus
from app.models.appointment import Appointment, AppointmentType, AppointmentStatus, CancelledBy
from app.models.specialty import Specialty
from app.models.promo_code import PromoCode, PromoType


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_appointment(
        self,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        appt_date: date,
        appt_time_str: str,
        appt_type: str,
        branch_id: Optional[uuid.UUID] = None,
        promo_code_str: Optional[str] = None,
    ) -> dict:
        """Book a new appointment with conflict detection."""

        # Verify doctor exists and is approved
        doctor = await self.db.get(Doctor, doctor_id)
        if not doctor:
            raise ValueError("DOCTOR_NOT_FOUND")
        if doctor.verification_status != VerificationStatus.APPROVED:
            raise ValueError("DOCTOR_NOT_APPROVED")

        # Parse time
        parts = appt_time_str.split(":")
        appt_time = time(int(parts[0]), int(parts[1]))

        # Conflict detection
        existing = await self.db.execute(
            select(Appointment).where(
                Appointment.doctor_id == doctor_id,
                Appointment.date == appt_date,
                Appointment.time == appt_time,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("SLOT_UNAVAILABLE")

        # Calculate amount
        amount = float(doctor.consultation_fee)
        discount = 0.0
        promo_code_id = None

        if promo_code_str:
            promo = await self._validate_promo(promo_code_str, amount)
            if promo:
                promo_code_id = promo["id"]
                discount = promo["discount"]

        final_amount = amount - discount

        # Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            branch_id=branch_id,
            date=appt_date,
            time=appt_time,
            type=AppointmentType(appt_type),
            status=AppointmentStatus.PENDING,
            amount=final_amount,
            discount_amount=discount,
            promo_code_id=promo_code_id,
        )
        self.db.add(appointment)
        await self.db.flush()

        # Increment promo usage
        if promo_code_id:
            result = await self.db.execute(
                select(PromoCode).where(PromoCode.id == promo_code_id)
            )
            promo_obj = result.scalar_one_or_none()
            if promo_obj:
                promo_obj.current_uses += 1

        await self.db.flush()
        return await self._format_appointment(appointment)

    async def list_appointments(
        self,
        user_id: uuid.UUID,
        role: UserRole,
        status_filter: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        """List appointments for a patient or doctor."""
        query = select(Appointment)

        if role == UserRole.PATIENT:
            query = query.where(Appointment.patient_id == user_id)
        else:
            query = query.where(Appointment.doctor_id == user_id)

        if status_filter:
            statuses = [s.strip() for s in status_filter.split(",")]
            query = query.where(Appointment.status.in_(statuses))

        # Count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Order + paginate
        query = query.order_by(Appointment.date.desc(), Appointment.time.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        appointments = result.scalars().all()

        formatted = []
        for appt in appointments:
            formatted.append(await self._format_appointment(appt))

        return formatted, total

    async def get_appointment(self, appt_id: uuid.UUID) -> Optional[dict]:
        """Get single appointment details."""
        appt = await self.db.get(Appointment, appt_id)
        if not appt:
            return None
        return await self._format_appointment(appt)

    async def update_status_by_doctor(
        self,
        appt_id: uuid.UUID,
        doctor_id: uuid.UUID,
        new_status: str,
        reason: Optional[str] = None,
    ) -> dict:
        """Doctor: confirm, complete, or cancel an appointment."""
        appt = await self.db.get(Appointment, appt_id)
        if not appt:
            raise ValueError("APPOINTMENT_NOT_FOUND")
        if appt.doctor_id != doctor_id:
            raise ValueError("NOT_YOUR_APPOINTMENT")

        target = AppointmentStatus(new_status)

        # Validate transitions
        valid_transitions = {
            AppointmentStatus.PENDING: [AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED],
            AppointmentStatus.CONFIRMED: [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED],
        }
        allowed = valid_transitions.get(appt.status, [])
        if target not in allowed:
            raise ValueError("INVALID_STATUS_TRANSITION")

        appt.status = target
        if target == AppointmentStatus.CANCELLED:
            appt.cancelled_by = CancelledBy.DOCTOR
            appt.cancel_reason = reason

        await self.db.flush()
        return await self._format_appointment(appt)

    async def cancel_by_patient(
        self,
        appt_id: uuid.UUID,
        patient_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> dict:
        """Patient cancels their appointment."""
        appt = await self.db.get(Appointment, appt_id)
        if not appt:
            raise ValueError("APPOINTMENT_NOT_FOUND")
        if appt.patient_id != patient_id:
            raise ValueError("NOT_YOUR_APPOINTMENT")
        if appt.status not in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED):
            raise ValueError("CANNOT_CANCEL")

        appt.status = AppointmentStatus.CANCELLED
        appt.cancelled_by = CancelledBy.PATIENT
        appt.cancel_reason = reason

        await self.db.flush()
        return await self._format_appointment(appt)

    async def _validate_promo(self, code: str, amount: float) -> Optional[dict]:
        """Validate and calculate promo code discount."""
        result = await self.db.execute(
            select(PromoCode).where(
                PromoCode.code == code.upper().strip(),
                PromoCode.is_active == True,
            )
        )
        promo = result.scalar_one_or_none()
        if not promo:
            return None

        now = datetime.now(timezone.utc)
        if now < promo.valid_from or now > promo.valid_until:
            return None
        if promo.max_uses and promo.current_uses >= promo.max_uses:
            return None
        if amount < float(promo.min_amount):
            return None

        if promo.type == PromoType.PERCENTAGE:
            discount = amount * float(promo.value)
            if promo.max_discount:
                discount = min(discount, float(promo.max_discount))
        else:
            discount = float(promo.value)

        discount = min(discount, amount)

        return {"id": promo.id, "discount": round(discount, 2)}

    async def _format_appointment(self, appt: Appointment) -> dict:
        """Format appointment for API response."""
        # Load doctor info
        doctor_user = await self.db.get(User, appt.doctor_id)
        doctor = await self.db.get(Doctor, appt.doctor_id)
        spec = None
        if doctor:
            spec = await self.db.get(Specialty, doctor.specialty_id)

        # Load patient info
        patient_user = await self.db.get(User, appt.patient_id)

        return {
            "id": appt.id,
            "patient_id": appt.patient_id,
            "doctor_id": appt.doctor_id,
            "branch_id": appt.branch_id,
            "date": str(appt.date),
            "time": appt.time.strftime("%H:%M"),
            "type": appt.type.value,
            "status": appt.status.value,
            "amount": float(appt.amount),
            "discount_amount": float(appt.discount_amount),
            "notes": appt.notes,
            "cancelled_by": appt.cancelled_by.value if appt.cancelled_by else None,
            "cancel_reason": appt.cancel_reason,
            "created_at": appt.created_at.isoformat() if appt.created_at else "",
            "doctor": {
                "id": doctor_user.id,
                "name": doctor_user.name,
                "avatar_url": doctor_user.avatar_url,
                "specialty_name_ar": spec.name_ar if spec else None,
                "specialty_name_en": spec.name_en if spec else None,
            } if doctor_user else None,
            "patient": {
                "id": patient_user.id,
                "name": patient_user.name,
                "phone": patient_user.phone,
                "avatar_url": patient_user.avatar_url,
            } if patient_user else None,
        }
