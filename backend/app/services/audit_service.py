"""Audit logging service — track admin actions, sensitive operations.

Usage:
    from app.services.audit_service import audit_log
    await audit_log(db, user_id=..., action="doctor.verify", entity_type="doctor", entity_id=..., new_data={...})
"""

import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def audit_log(
    db: AsyncSession,
    action: str,
    entity_type: str,
    user_id: Optional[uuid.UUID] = None,
    entity_id: Optional[uuid.UUID] = None,
    old_data: Optional[dict] = None,
    new_data: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Create an audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry


async def list_audit_logs(
    db: AsyncSession,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    action: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> tuple:
    """Query audit logs with filters."""
    base = select(AuditLog)

    if entity_type:
        base = base.where(AuditLog.entity_type == entity_type)
    if entity_id:
        base = base.where(AuditLog.entity_id == entity_id)
    if user_id:
        base = base.where(AuditLog.user_id == user_id)
    if action:
        base = base.where(AuditLog.action.ilike(f"%{action}%"))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = base.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    data = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "old_data": log.old_data,
            "new_data": log.new_data,
            "ip_address": str(log.ip_address) if log.ip_address else None,
            "created_at": log.created_at.isoformat() if log.created_at else "",
        }
        for log in logs
    ]
    return data, total
