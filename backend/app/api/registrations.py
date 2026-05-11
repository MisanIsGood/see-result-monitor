"""
Registration API routes.
Handles creating, listing and fetching SEE result monitoring registrations.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.registration import Registration
from app.utils.schemas import (
    RegistrationCreate,
    RegistrationResponse,
    RegistrationStatus,
    MessageResponse,
)

router = APIRouter(prefix="/registrations", tags=["Registrations"])


@router.post("/", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def create_registration(
    payload: RegistrationCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a student for SEE result monitoring.
    Prevents duplicate entries for the same symbol number + email combo.
    """
    # Duplicate check
    stmt = select(Registration).where(
        Registration.symbol_number == payload.symbol_number,
        Registration.receiver_email == payload.receiver_email,
        Registration.is_active == True,
    )
    existing = (await db.execute(stmt)).scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An active monitoring request already exists for symbol "
                f"{payload.symbol_number} → {payload.receiver_email}."
            ),
        )

    reg = Registration(
        receiver_email=str(payload.receiver_email),
        symbol_number=payload.symbol_number,
        date_of_birth=payload.date_of_birth,
    )
    db.add(reg)
    await db.flush()
    await db.refresh(reg)
    return reg


@router.get("/", response_model=List[RegistrationResponse])
async def list_registrations(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all registrations (newest first)."""
    stmt = (
        select(Registration)
        .order_by(Registration.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return rows


@router.get("/{registration_id}", response_model=RegistrationStatus)
async def get_registration(
    registration_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed status of a single registration."""
    reg = await db.get(Registration, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found.")
    return reg


@router.get("/symbol/{symbol_number}", response_model=List[RegistrationStatus])
async def get_by_symbol(
    symbol_number: str,
    db: AsyncSession = Depends(get_db),
):
    """Find all registrations for a given symbol number."""
    stmt = select(Registration).where(Registration.symbol_number == symbol_number)
    rows = (await db.execute(stmt)).scalars().all()
    return rows


@router.delete("/{registration_id}", response_model=MessageResponse)
async def cancel_registration(
    registration_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel / deactivate a monitoring registration."""
    reg = await db.get(Registration, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found.")

    reg.is_active = False
    await db.flush()
    return {"message": f"Registration {registration_id} cancelled.", "success": True}
