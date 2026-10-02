import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: uuid.UUID


class PaymentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    amount: Decimal
    status: PaymentStatus
    transaction_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookPayload(BaseModel):
    transaction_id: str
    status: PaymentStatus
    idempotency_key: str
