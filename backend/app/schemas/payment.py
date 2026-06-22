"""Payment schemas."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PaymentInitiateRequest(BaseModel):
    appointment_id: UUID
    payment_method: str = Field(..., pattern="^(card|fawry|wallet)$")


class PaymentInitiateResponse(BaseModel):
    payment_id: UUID
    payment_url: Optional[str] = None
    transaction_id: Optional[str] = None
    amount: float
    currency: str = "EGP"
    status: str


class PaymentWebhookPayload(BaseModel):
    """Generic webhook payload — actual shape depends on gateway."""
    transaction_id: str
    status: str
    amount: Optional[float] = None
    metadata: Optional[dict] = None


class PaymentOut(BaseModel):
    id: UUID
    appointment_id: UUID
    patient_id: UUID
    amount: float
    currency: str
    payment_method: str
    payment_gateway: str
    gateway_transaction_id: Optional[str] = None
    status: str
    paid_at: Optional[str] = None
    refunded_at: Optional[str] = None
    refund_amount: Optional[float] = None
    created_at: str

    model_config = {"from_attributes": True}


class RefundRequest(BaseModel):
    payment_id: UUID
    amount: Optional[float] = Field(None, gt=0, description="Partial refund amount. Omit for full refund.")
    reason: Optional[str] = None
