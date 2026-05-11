"""
Monitor control API routes.
Start / stop / status of the background monitoring loop.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.registration import Registration
from app.services import monitor as mon
from app.core.config import settings
from app.utils.schemas import MonitorStatusResponse, MonitorControlResponse

router = APIRouter(prefix="/monitor", tags=["Monitor"])


@router.get("/status", response_model=MonitorStatusResponse)
async def monitor_status(db: AsyncSession = Depends(get_db)):
    """Return current monitoring status and stats."""
    count_stmt = select(func.count()).where(
        Registration.is_active == True,
        Registration.result_found == False,
    )
    active_count = (await db.execute(count_stmt)).scalar() or 0

    running = mon.is_monitoring()
    return MonitorStatusResponse(
        is_monitoring=running,
        active_registrations=active_count,
        interval_seconds=settings.MONITOR_INTERVAL_SECONDS,
        message=(
            f"Monitoring is {'running' if running else 'stopped'}. "
            f"{active_count} active registration(s) queued."
        ),
    )


@router.post("/start", response_model=MonitorControlResponse)
async def start_monitor():
    """Start the background monitoring loop."""
    started = mon.start_monitoring()
    running = mon.is_monitoring()
    return MonitorControlResponse(
        success=True,
        message="Monitoring started." if started else "Monitoring was already running.",
        is_monitoring=running,
    )


@router.post("/stop", response_model=MonitorControlResponse)
async def stop_monitor():
    """Stop the background monitoring loop."""
    stopped = mon.stop_monitoring()
    return MonitorControlResponse(
        success=True,
        message="Monitoring stopped." if stopped else "Monitoring was not running.",
        is_monitoring=False,
    )
