"""Branch service — CRUD, schedules, toggle active."""

import uuid
from datetime import time, datetime, timezone
from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch, BranchSchedule


class BranchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_branches(self, doctor_id: uuid.UUID) -> List[dict]:
        """List all branches for a doctor."""
        result = await self.db.execute(
            select(Branch)
            .where(Branch.doctor_id == doctor_id, Branch.deleted_at == None)
            .order_by(Branch.created_at)
        )
        branches = result.scalars().all()
        out = []
        for b in branches:
            # Load schedules
            sched_result = await self.db.execute(
                select(BranchSchedule)
                .where(BranchSchedule.branch_id == b.id)
                .order_by(BranchSchedule.day_of_week)
            )
            schedules = sched_result.scalars().all()
            out.append(self._format_branch(b, schedules))
        return out

    async def create_branch(self, doctor_id: uuid.UUID, data: dict) -> dict:
        """Create a new branch with schedules."""
        branch = Branch(
            doctor_id=doctor_id,
            name=data["name"],
            governorate=data["governorate"],
            area=data["area"],
            address=data["address"],
            phone=data["phone"],
            consultation_fee=data["consultation_fee"],
        )
        self.db.add(branch)
        await self.db.flush()

        # Add schedules
        schedules = []
        for wd in data.get("working_days", []):
            s_parts = wd["start"].split(":")
            e_parts = wd["end"].split(":")
            sched = BranchSchedule(
                branch_id=branch.id,
                day_of_week=wd["day"],
                start_time=time(int(s_parts[0]), int(s_parts[1])),
                end_time=time(int(e_parts[0]), int(e_parts[1])),
                slot_duration_minutes=wd.get("slot_duration", 30),
            )
            self.db.add(sched)
            schedules.append(sched)

        await self.db.flush()
        return self._format_branch(branch, schedules)

    async def update_branch(
        self, branch_id: uuid.UUID, doctor_id: uuid.UUID, data: dict
    ) -> Optional[dict]:
        """Update branch details and optionally replace schedules."""
        branch = await self._get_owned_branch(branch_id, doctor_id)
        if not branch:
            return None

        for field in ["name", "governorate", "area", "address", "phone", "consultation_fee"]:
            if field in data and data[field] is not None:
                setattr(branch, field, data[field])

        # Replace schedules if provided
        if "working_days" in data and data["working_days"] is not None:
            await self.db.execute(
                delete(BranchSchedule).where(BranchSchedule.branch_id == branch_id)
            )
            for wd in data["working_days"]:
                s_parts = wd["start"].split(":")
                e_parts = wd["end"].split(":")
                sched = BranchSchedule(
                    branch_id=branch_id,
                    day_of_week=wd["day"],
                    start_time=time(int(s_parts[0]), int(s_parts[1])),
                    end_time=time(int(e_parts[0]), int(e_parts[1])),
                    slot_duration_minutes=wd.get("slot_duration", 30),
                )
                self.db.add(sched)

        await self.db.flush()

        # Reload schedules
        sched_result = await self.db.execute(
            select(BranchSchedule)
            .where(BranchSchedule.branch_id == branch_id)
            .order_by(BranchSchedule.day_of_week)
        )
        return self._format_branch(branch, sched_result.scalars().all())

    async def toggle_active(
        self, branch_id: uuid.UUID, doctor_id: uuid.UUID
    ) -> Optional[dict]:
        """Toggle branch active/inactive."""
        branch = await self._get_owned_branch(branch_id, doctor_id)
        if not branch:
            return None
        branch.is_active = not branch.is_active
        await self.db.flush()
        return {"id": branch.id, "is_active": branch.is_active}

    async def delete_branch(
        self, branch_id: uuid.UUID, doctor_id: uuid.UUID
    ) -> bool:
        """Soft delete a branch."""
        branch = await self._get_owned_branch(branch_id, doctor_id)
        if not branch:
            return False
        branch.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def _get_owned_branch(
        self, branch_id: uuid.UUID, doctor_id: uuid.UUID
    ) -> Optional[Branch]:
        result = await self.db.execute(
            select(Branch).where(
                Branch.id == branch_id,
                Branch.doctor_id == doctor_id,
                Branch.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _format_branch(branch: Branch, schedules: list) -> dict:
        return {
            "id": branch.id,
            "name": branch.name,
            "governorate": branch.governorate,
            "area": branch.area,
            "address": branch.address,
            "phone": branch.phone,
            "consultation_fee": float(branch.consultation_fee),
            "is_active": branch.is_active,
            "schedules": [
                {
                    "day_of_week": s.day_of_week,
                    "start_time": s.start_time.strftime("%H:%M"),
                    "end_time": s.end_time.strftime("%H:%M"),
                    "slot_duration_minutes": s.slot_duration_minutes,
                    "is_active": s.is_active,
                }
                for s in schedules
            ],
        }
