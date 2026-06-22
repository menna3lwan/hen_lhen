"""Payment service — initiation, webhook processing, history, refunds.

Payment gateway integration is abstracted behind PaymentGateway protocol.
Currently ships with a MockGateway for development; swap in PaymobGateway
or FawryGateway for production.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Protocol

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus
from app.models.appointment import Appointment, AppointmentStatus


# ── Gateway Protocol ──

class PaymentGateway(Protocol):
    """Interface that any payment gateway must implement."""

    async def create_payment(
        self, amount: float, currency: str, method: str,
        metadata: dict,
    ) -> dict:
        """Returns {payment_url, transaction_id, status}."""
        ...

    async def verify_payment(self, transaction_id: str) -> dict:
        """Returns {status, amount, paid_at}."""
        ...

    async def refund_payment(
        self, transaction_id: str, amount: float,
    ) -> dict:
        """Returns {status, refund_id}."""
        ...


# ── Mock Gateway (development) ──

class MockGateway:
    """Mock payment gateway for development/testing."""

    async def create_payment(
        self, amount: float, currency: str, method: str,
        metadata: dict,
    ) -> dict:
        txn_id = f"mock_txn_{uuid.uuid4().hex[:12]}"
        return {
            "payment_url": f"https://pay.mock.dev/checkout/{txn_id}",
            "transaction_id": txn_id,
            "status": "pending",
        }

    async def verify_payment(self, transaction_id: str) -> dict:
        return {
            "status": "completed",
            "amount": None,
            "paid_at": datetime.now(timezone.utc).isoformat(),
        }

    async def refund_payment(
        self, transaction_id: str, amount: float,
    ) -> dict:
        return {
            "status": "refunded",
            "refund_id": f"mock_ref_{uuid.uuid4().hex[:8]}",
        }


# ── Service ──

class PaymentService:
    def __init__(self, db: AsyncSession, gateway: Optional[PaymentGateway] = None):
        self.db = db
        self.gateway = gateway or MockGateway()

    async def initiate_payment(
        self,
        patient_id: uuid.UUID,
        appointment_id: uuid.UUID,
        payment_method: str,
    ) -> dict:
        """Create a payment for an appointment."""
        appt = await self.db.get(Appointment, appointment_id)
        if not appt:
            raise ValueError("APPOINTMENT_NOT_FOUND")
        if appt.patient_id != patient_id:
            raise ValueError("NOT_YOUR_APPOINTMENT")
        if appt.status == AppointmentStatus.CANCELLED:
            raise ValueError("APPOINTMENT_CANCELLED")

        # Check for existing non-failed payment
        existing = await self.db.execute(
            select(Payment).where(
                Payment.appointment_id == appointment_id,
                Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.COMPLETED]),
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("PAYMENT_ALREADY_EXISTS")

        amount = float(appt.amount)

        # Call gateway
        gw_result = await self.gateway.create_payment(
            amount=amount,
            currency="EGP",
            method=payment_method,
            metadata={
                "appointment_id": str(appointment_id),
                "patient_id": str(patient_id),
            },
        )

        # Store payment
        payment = Payment(
            appointment_id=appointment_id,
            patient_id=patient_id,
            amount=amount,
            currency="EGP",
            payment_method=payment_method,
            payment_gateway="mock",  # swap to "paymob"/"fawry" in production
            gateway_transaction_id=gw_result["transaction_id"],
            status=PaymentStatus.PENDING,
        )
        self.db.add(payment)
        await self.db.flush()

        return {
            "payment_id": payment.id,
            "payment_url": gw_result.get("payment_url"),
            "transaction_id": gw_result["transaction_id"],
            "amount": amount,
            "currency": "EGP",
            "status": "pending",
        }

    async def process_webhook(self, transaction_id: str, status: str) -> dict:
        """Process payment gateway webhook callback."""
        result = await self.db.execute(
            select(Payment).where(
                Payment.gateway_transaction_id == transaction_id
            )
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise ValueError("PAYMENT_NOT_FOUND")

        if status == "completed":
            payment.status = PaymentStatus.COMPLETED
            payment.paid_at = datetime.now(timezone.utc)

            # Confirm the appointment automatically
            appt = await self.db.get(Appointment, payment.appointment_id)
            if appt and appt.status == AppointmentStatus.PENDING:
                appt.status = AppointmentStatus.CONFIRMED
        elif status == "failed":
            payment.status = PaymentStatus.FAILED
        elif status == "refunded":
            payment.status = PaymentStatus.REFUNDED
            payment.refunded_at = datetime.now(timezone.utc)

        await self.db.flush()

        return {
            "payment_id": str(payment.id),
            "status": payment.status.value,
        }

    async def get_payment_history(
        self,
        patient_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        """List payment history for a patient."""
        base = select(Payment).where(Payment.patient_id == patient_id)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = base.order_by(Payment.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(query)
        payments = result.scalars().all()

        data = [self._format_payment(p) for p in payments]
        return data, total

    async def refund_payment(
        self,
        payment_id: uuid.UUID,
        amount: Optional[float] = None,
    ) -> dict:
        """Refund a payment (full or partial)."""
        payment = await self.db.get(Payment, payment_id)
        if not payment:
            raise ValueError("PAYMENT_NOT_FOUND")
        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError("PAYMENT_NOT_COMPLETED")

        refund_amount = amount or float(payment.amount)
        if refund_amount > float(payment.amount):
            raise ValueError("REFUND_EXCEEDS_AMOUNT")

        # Call gateway
        gw_result = await self.gateway.refund_payment(
            transaction_id=payment.gateway_transaction_id,
            amount=refund_amount,
        )

        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = datetime.now(timezone.utc)
        payment.refund_amount = refund_amount

        await self.db.flush()
        return self._format_payment(payment)

    @staticmethod
    def _format_payment(p: Payment) -> dict:
        return {
            "id": p.id,
            "appointment_id": p.appointment_id,
            "patient_id": p.patient_id,
            "amount": float(p.amount),
            "currency": p.currency,
            "payment_method": p.payment_method,
            "payment_gateway": p.payment_gateway,
            "gateway_transaction_id": p.gateway_transaction_id,
            "status": p.status.value,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "refunded_at": p.refunded_at.isoformat() if p.refunded_at else None,
            "refund_amount": float(p.refund_amount) if p.refund_amount else None,
            "created_at": p.created_at.isoformat() if p.created_at else "",
        }
