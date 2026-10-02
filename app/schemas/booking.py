import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    test_id: uuid.UUID
    centre_id: uuid.UUID
    appointment_time: datetime


class BookingResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    test_id: uuid.UUID
    centre_id: uuid.UUID
    appointment_time: datetime
    amount: Decimal
    status: BookingStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookingDetailResponse(BookingResponse):
    test_name: str | None = None
    centre_name: str | None = None
    patient_name: str | None = None
