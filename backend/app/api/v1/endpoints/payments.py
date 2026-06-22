"""Payment endpoints — initiate, webhook, history, refund."""

import uuid
import hmac
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.deps import get_current_patient, get_current_admin
from app.models.user import User
from app.schemas.payment import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentWebhookPayload,
    PaymentOut,
    RefundRequest,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])

ERROR_MAP = {
    "APPOINTMENT_NOT_FOUND": (404, "Appointment not found", "الموعد غير موجود"),
    "NOT_YOUR_APPOINTMENT": (403, "Not your appointment", "هذا ليس موعدك"),
    "APPOINTMENT_CANCELLED": (400, "Appointment is cancelled", "الموعد ملغي"),
    "PAYMENT_ALREADY_EXISTS": (409, "Payment already exists", "يوجد دفع بالفعل لهذا الموعد"),
    "PAYMENT_NOT_FOUND": (404, "Payment not found", "الدفع غير موجود"),
    "PAYMENT_NOT_COMPLETED": (400, "Payment not completed", "الدفع لم يكتمل بعد"),
    "REFUND_EXCEEDS_AMOUNT": (400, "Refund exceeds payment amount", "مبلغ الاسترداد أكبر من قيمة الدفع"),
}


def _raise(code: str):
    status, msg, msg_ar = ERROR_MAP[code]
    raise HTTPException(status_code=status, detail={
        "code": code, "message": msg, "message_ar": msg_ar,
    })


@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=201)
async def initiate_payment(
    body: PaymentInitiateRequest,
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a payment for an appointment."""
    svc = PaymentService(db)
    try:
        result = await svc.initiate_payment(
            patient_id=current_user.id,
            appointment_id=body.appointment_id,
            payment_method=body.payment_method,
        )
    except ValueError as e:
        _raise(str(e))

    await db.commit()
    return result


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    body: PaymentWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """Process payment gateway webhook with HMAC signature verification.

    When X-Webhook-Signature header is present and PAYMENT_WEBHOOK_SECRET
    is configured, the signature is verified. Without the header, the
    request proceeds (allows dev/test usage).
    """
    from app.core.config import settings

    # Verify HMAC signature when header is present
    signature = request.headers.get("X-Webhook-Signature")
    if signature and settings.PAYMENT_WEBHOOK_SECRET:
        raw_body = await request.body()
        expected = hmac.new(
            settings.PAYMENT_WEBHOOK_SECRET.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail={
                "code": "INVALID_SIGNATURE",
                "message": "Invalid webhook signature",
                "message_ar": "توقيع الويب هوك غير صالح",
            })

    svc = PaymentService(db)
    try:
        result = await svc.process_webhook(
            transaction_id=body.transaction_id,
            status=body.status,
        )
    except ValueError as e:
        _raise(str(e))

    await db.commit()
    return result


@router.get("/history", response_model=PaginatedResponse)
async def payment_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Get payment history for current patient."""
    svc = PaymentService(db)
    data, total = await svc.get_payment_history(
        patient_id=current_user.id, page=page, limit=limit,
    )
    pages = (total + limit - 1) // limit if limit else 1
    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(total=total, page=page, limit=limit, pages=pages),
    )


@router.post("/refund")
async def refund_payment(
    body: RefundRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Refund a payment (admin only)."""
    svc = PaymentService(db)
    try:
        result = await svc.refund_payment(
            payment_id=body.payment_id,
            amount=body.amount,
        )
    except ValueError as e:
        _raise(str(e))

    await db.commit()
    return result
