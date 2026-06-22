"""Medical Record service — create, read, update records & prescriptions."""

import uuid
from typing import List, Tuple, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord, RecordType
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole


class MedicalRecordService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_record(
        self,
        doctor_id: uuid.UUID,
        appointment_id: uuid.UUID,
        record_type: str,
        diagnosis: Optional[str] = None,
        notes: Optional[str] = None,
        prescriptions: Optional[list] = None,
        attachments: Optional[list] = None,
        is_private: bool = False,
        follow_up_date=None,
    ) -> dict:
        """Create a medical record (doctor only, for completed/confirmed appointments)."""
        appt = await self.db.get(Appointment, appointment_id)
        if not appt:
            raise ValueError("APPOINTMENT_NOT_FOUND")
        if appt.doctor_id != doctor_id:
            raise ValueError("NOT_YOUR_APPOINTMENT")
        if appt.status not in (AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED):
            raise ValueError("APPOINTMENT_NOT_COMPLETED")

        # Check for existing record of same type
        existing = await self.db.execute(
            select(MedicalRecord).where(
                MedicalRecord.appointment_id == appointment_id,
                MedicalRecord.type == RecordType(record_type),
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("RECORD_ALREADY_EXISTS")

        # Serialize prescriptions to JSON-compatible format
        rx_data = None
        if prescriptions:
            rx_data = [p.dict() if hasattr(p, 'dict') else p for p in prescriptions]

        record = MedicalRecord(
            appointment_id=appointment_id,
            patient_id=appt.patient_id,
            doctor_id=doctor_id,
            type=RecordType(record_type),
            diagnosis=diagnosis,
            notes=notes,
            prescriptions=rx_data,
            attachments=attachments,
            is_private=is_private,
            follow_up_date=follow_up_date,
        )
        self.db.add(record)
        await self.db.flush()

        return await self._format(record)

    async def get_record(
        self, record_id: uuid.UUID, user_id: uuid.UUID, user_role: str,
    ) -> dict:
        """Get a single record (accessible to doctor who created it or patient)."""
        record = await self.db.get(MedicalRecord, record_id)
        if not record:
            raise ValueError("RECORD_NOT_FOUND")

        if user_role == UserRole.PATIENT and record.patient_id != user_id:
            raise ValueError("NOT_YOUR_RECORD")
        if user_role == UserRole.DOCTOR and record.doctor_id != user_id:
            raise ValueError("NOT_YOUR_RECORD")

        return await self._format(record)

    async def list_patient_records(
        self,
        patient_id: uuid.UUID,
        viewer_id: uuid.UUID,
        viewer_role: str,
        page: int = 1,
        limit: int = 20,
        record_type: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """List medical records for a patient."""
        # Patients see their own; doctors see records they created
        base = select(MedicalRecord).where(MedicalRecord.patient_id == patient_id)

        if viewer_role == UserRole.DOCTOR:
            base = base.where(MedicalRecord.doctor_id == viewer_id)
        elif viewer_role == UserRole.PATIENT and viewer_id != patient_id:
            raise ValueError("NOT_YOUR_RECORDS")

        if record_type:
            base = base.where(MedicalRecord.type == RecordType(record_type))

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = base.order_by(MedicalRecord.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        records = result.scalars().all()

        data = []
        for r in records:
            data.append(await self._format(r))
        return data, total

    async def list_by_appointment(
        self, appointment_id: uuid.UUID, user_id: uuid.UUID,
    ) -> List[dict]:
        """Get all records for an appointment."""
        appt = await self.db.get(Appointment, appointment_id)
        if not appt:
            raise ValueError("APPOINTMENT_NOT_FOUND")
        if appt.patient_id != user_id and appt.doctor_id != user_id:
            raise ValueError("NOT_YOUR_APPOINTMENT")

        result = await self.db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.appointment_id == appointment_id)
            .order_by(MedicalRecord.created_at.asc())
        )
        records = result.scalars().all()
        return [await self._format(r) for r in records]

    async def update_record(
        self, record_id: uuid.UUID, doctor_id: uuid.UUID, **kwargs,
    ) -> dict:
        """Update a record (doctor who created it only)."""
        record = await self.db.get(MedicalRecord, record_id)
        if not record:
            raise ValueError("RECORD_NOT_FOUND")
        if record.doctor_id != doctor_id:
            raise ValueError("NOT_YOUR_RECORD")

        for field in ("diagnosis", "notes", "attachments", "follow_up_date"):
            if field in kwargs and kwargs[field] is not None:
                setattr(record, field, kwargs[field])

        if "prescriptions" in kwargs and kwargs["prescriptions"] is not None:
            rx_data = [p.dict() if hasattr(p, 'dict') else p for p in kwargs["prescriptions"]]
            record.prescriptions = rx_data

        await self.db.flush()
        return await self._format(record)

    async def _format(self, r: MedicalRecord) -> dict:
        # Load names
        doctor = await self.db.get(User, r.doctor_id)
        patient = await self.db.get(User, r.patient_id)

        return {
            "id": r.id,
            "appointment_id": r.appointment_id,
            "patient_id": r.patient_id,
            "doctor_id": r.doctor_id,
            "doctor_name": doctor.name if doctor else None,
            "patient_name": patient.name if patient else None,
            "type": r.type.value,
            "diagnosis": r.diagnosis,
            "notes": r.notes,
            "prescriptions": r.prescriptions,
            "attachments": r.attachments,
            "is_private": r.is_private,
            "follow_up_date": r.follow_up_date.isoformat() if r.follow_up_date else None,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "updated_at": r.updated_at.isoformat() if r.updated_at else "",
        }
