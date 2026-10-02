import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.centre import DiagnosticCentre, DiagnosticTest
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse, BookingDetailResponse
from app.security import get_current_user

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.appointment_time.tzinfo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment time must include timezone")

    if payload.appointment_time < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment time must be in the future")

    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == payload.test_id).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic test not found")

    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == payload.centre_id).first()
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic centre not found")

    if test.centre_id != centre.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This test is not available at the selected centre",
        )

    booking = Booking(
        user_id=current_user.id,
        test_id=test.id,
        centre_id=centre.id,
        appointment_time=payload.appointment_time,
        amount=test.price,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/", response_model=list[BookingDetailResponse])
def list_my_bookings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: BookingStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Booking).filter(Booking.user_id == current_user.id)
    if status_filter:
        query = query.filter(Booking.status == status_filter)

    bookings = query.order_by(Booking.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return [_to_detail(b) for b in bookings]


@router.get("/{booking_id}", response_model=BookingDetailResponse)
def get_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this booking")
    return _to_detail(booking)


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this booking")

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is already cancelled")
    if booking.status == BookingStatus.CONFIRMED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a confirmed booking")

    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return booking


def _to_detail(booking: Booking) -> BookingDetailResponse:
    return BookingDetailResponse(
        id=booking.id,
        user_id=booking.user_id,
        test_id=booking.test_id,
        centre_id=booking.centre_id,
        appointment_time=booking.appointment_time,
        amount=booking.amount,
        status=booking.status,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        test_name=booking.test.name if booking.test else None,
        centre_name=booking.centre.name if booking.centre else None,
        patient_name=booking.user.full_name if booking.user else None,
    )
