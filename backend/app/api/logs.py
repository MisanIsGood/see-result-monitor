"""
Admin logs API routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.log import ActivityLog
from app.utils.schemas import ActivityLogResponse

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/", response_model=List[ActivityLogResponse])
async def get_logs(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    symbol_number: Optional[str] = Query(None, description="Filter by symbol number"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve activity logs, newest first."""
    stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit)

    if event_type:
        stmt = stmt.where(ActivityLog.event_type == event_type.upper())
    if symbol_number:
        stmt = stmt.where(ActivityLog.symbol_number == symbol_number)

    rows = (await db.execute(stmt)).scalars().all()
    return rows
