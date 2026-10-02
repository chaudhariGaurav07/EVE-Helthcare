import uuid
import random
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, WebhookPayload
from app.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def initiate_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == payload.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to pay for this booking")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pay for a booking with status {booking.status.value}",
        )

    existing_payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if existing_payment:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment already exists for this booking")

    simulated_success = random.random() < 0.8
    payment_status = PaymentStatus.SUCCESS if simulated_success else PaymentStatus.FAILED
    transaction_id = f"txn_{uuid.uuid4().hex[:16]}"

    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=payment_status,
        transaction_id=transaction_id,
        idempotency_key=f"pay_{booking.id}",
    )
    db.add(payment)

    if payment_status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED

    db.commit()
    db.refresh(payment)
    logger.info(f"Payment {transaction_id} for booking {booking.id}: {payment_status.value}")
    return payment


@router.post("/webhook/", status_code=status.HTTP_200_OK)
def payment_webhook(payload: WebhookPayload, db: Session = Depends(get_db)):
    existing = db.query(Payment).filter(Payment.idempotency_key == payload.idempotency_key).first()
    if existing and existing.status != PaymentStatus.PENDING:
        logger.info(f"Duplicate webhook ignored for idempotency_key={payload.idempotency_key}")
        return {"message": "Event already processed", "payment_id": str(existing.id)}

    payment = db.query(Payment).filter(Payment.transaction_id == payload.transaction_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found for given transaction_id")

    if payment.status != PaymentStatus.PENDING:
        logger.info(f"Webhook for already-settled payment {payment.transaction_id}, skipping")
        return {"message": "Payment already settled", "payment_id": str(payment.id)}

    payment.status = payload.status
    payment.idempotency_key = payload.idempotency_key

    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if booking:
        if payload.status == PaymentStatus.SUCCESS:
            booking.status = BookingStatus.CONFIRMED
        elif payload.status == PaymentStatus.FAILED:
            booking.status = BookingStatus.FAILED

    db.commit()
    db.refresh(payment)
    logger.info(f"Webhook processed: payment {payment.transaction_id} -> {payload.status.value}")
    return {"message": "Webhook processed", "payment_id": str(payment.id)}


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment")
    return payment
