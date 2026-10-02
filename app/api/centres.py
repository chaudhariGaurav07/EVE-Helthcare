from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.centre import DiagnosticCentre, DiagnosticTest
from app.schemas.centre import (
    CentreCreate,
    CentreResponse,
    CentreListResponse,
    DiagnosticTestCreate,
    DiagnosticTestResponse,
)
from app.security import get_current_user
from app.models.user import User

import uuid

router = APIRouter(prefix="/centres", tags=["Diagnostic Centres"])


@router.post("/", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
def create_centre(
    payload: CentreCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    centre = DiagnosticCentre(
        name=payload.name,
        location=payload.location,
        address=payload.address,
    )
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


@router.get("/", response_model=list[CentreListResponse])
def list_centres(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    location: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(DiagnosticCentre)
    if location:
        query = query.filter(DiagnosticCentre.location.ilike(f"%{location}%"))

    centres = query.offset((page - 1) * size).limit(size).all()
    result = []
    for c in centres:
        result.append(CentreListResponse(
            id=c.id,
            name=c.name,
            location=c.location,
            address=c.address,
            test_count=len(c.tests),
        ))
    return result


@router.get("/{centre_id}", response_model=CentreResponse)
def get_centre(centre_id: uuid.UUID, db: Session = Depends(get_db)):
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    return centre


@router.post("/{centre_id}/tests", response_model=DiagnosticTestResponse, status_code=status.HTTP_201_CREATED)
def add_test_to_centre(
    centre_id: uuid.UUID,
    payload: DiagnosticTestCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")

    test = DiagnosticTest(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        centre_id=centre_id,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.get("/{centre_id}/tests", response_model=list[DiagnosticTestResponse])
def list_tests_for_centre(centre_id: uuid.UUID, db: Session = Depends(get_db)):
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    return centre.tests
