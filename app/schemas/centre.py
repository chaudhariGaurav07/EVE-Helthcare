import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class DiagnosticTestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal = Field(gt=0, decimal_places=2)


class DiagnosticTestResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    centre_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class CentreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=500)


class CentreResponse(BaseModel):
    id: uuid.UUID
    name: str
    location: str
    address: str | None
    created_at: datetime
    tests: list[DiagnosticTestResponse] = []

    model_config = {"from_attributes": True}


class CentreListResponse(BaseModel):
    id: uuid.UUID
    name: str
    location: str
    address: str | None
    test_count: int = 0

    model_config = {"from_attributes": True}
