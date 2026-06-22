"""Branch endpoints (doctor only)."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_doctor
from app.models.user import User
from app.services.branch_service import BranchService
from app.schemas.branch import (
    BranchCreateRequest, BranchUpdateRequest, BranchOut,
)
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/branches", tags=["Branches"])


@router.get("", response_model=List[BranchOut])
async def list_branches(
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """List current doctor's branches."""
    service = BranchService(db)
    branches = await service.list_branches(current_user.id)
    return [BranchOut(**b) for b in branches]


@router.post("", response_model=BranchOut, status_code=201)
async def create_branch(
    body: BranchCreateRequest,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Create a new branch."""
    service = BranchService(db)
    result = await service.create_branch(
        current_user.id,
        body.model_dump(),
    )
    return BranchOut(**result)


@router.put("/{branch_id}", response_model=BranchOut)
async def update_branch(
    branch_id: uuid.UUID,
    body: BranchUpdateRequest,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Update a branch."""
    service = BranchService(db)
    result = await service.update_branch(
        branch_id, current_user.id, body.model_dump(exclude_unset=True),
    )
    if not result:
        raise HTTPException(status_code=404, detail={
            "code": "BRANCH_NOT_FOUND", "message": "Branch not found",
            "message_ar": "الفرع غير موجود",
        })
    return BranchOut(**result)


@router.patch("/{branch_id}/toggle-active")
async def toggle_active(
    branch_id: uuid.UUID,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Toggle branch active/inactive."""
    service = BranchService(db)
    result = await service.toggle_active(branch_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail={
            "code": "BRANCH_NOT_FOUND", "message": "Branch not found",
            "message_ar": "الفرع غير موجود",
        })
    return result


@router.delete("/{branch_id}", response_model=MessageResponse)
async def delete_branch(
    branch_id: uuid.UUID,
    current_user: User = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a branch."""
    service = BranchService(db)
    deleted = await service.delete_branch(branch_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail={
            "code": "BRANCH_NOT_FOUND", "message": "Branch not found",
            "message_ar": "الفرع غير موجود",
        })
    return MessageResponse(message="Branch deleted", message_ar="تم حذف الفرع")
