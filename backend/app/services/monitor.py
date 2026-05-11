"""
Background monitoring service.
Periodically checks all active registrations for SEE results
and sends email notifications when results are published.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.models.registration import Registration
from app.models.log import ActivityLog
from app.services.scraper import check_result_with_retry
from app.services.email_service import send_result_email

logger = logging.getLogger(__name__)

_monitoring_task: asyncio.Task = None
_is_monitoring = False


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

async def _log_event(
    session: AsyncSession,
    event_type: str,
    message: str,
    registration_id: int = None,
    symbol_number: str = None,
    source_url: str = None,
):
    log = ActivityLog(
        registration_id=registration_id,
        event_type=event_type,
        message=message,
        symbol_number=symbol_number,
        source_url=source_url,
    )
    session.add(log)
    await session.flush()


# ---------------------------------------------------------------------------
# Single registration check
# ---------------------------------------------------------------------------

async def _process_registration(reg: Registration) -> None:
    """Check one registration and update its state in the database."""
    async with AsyncSessionLocal() as session:
        try:
            await _log_event(
                session,
                event_type="CHECK_STARTED",
                message=f"Checking SEE result for symbol {reg.symbol_number}",
                registration_id=reg.id,
                symbol_number=reg.symbol_number,
            )

            result = await check_result_with_retry(reg.symbol_number, reg.date_of_birth)

            now = datetime.now(timezone.utc)

            if result and result.found:
                # Serialize result to JSON
                result_json = json.dumps({
                    "name": result.name,
                    "school": result.school,
                    "district": result.district,
                    "gpa": result.gpa,
                    "grade": result.grade,
                    "result_status": result.result_status,
                    "subjects": result.subjects,
                    "source_url": result.source_url,
                })

                # Update registration record
                await session.execute(
                    update(Registration)
                    .where(Registration.id == reg.id)
                    .values(
                        result_found=True,
                        result_data=result_json,
                        last_checked_at=now,
                        check_count=reg.check_count + 1,
                        last_error=None,
                    )
                )

                await _log_event(
                    session,
                    event_type="RESULT_FOUND",
                    message=f"Result found for {reg.symbol_number}: GPA={result.gpa}, Grade={result.grade}",
                    registration_id=reg.id,
                    symbol_number=reg.symbol_number,
                    source_url=result.source_url,
                )

                # Send email notification
                email_ok = await send_result_email(
                    to_email=reg.receiver_email,
                    result=result,
                    symbol_number=reg.symbol_number,
                )

                if email_ok:
                    await session.execute(
                        update(Registration)
                        .where(Registration.id == reg.id)
                        .values(email_sent=True, is_active=False)  # Deactivate after success
                    )
                    await _log_event(
                        session,
                        event_type="EMAIL_SENT",
                        message=f"Result email sent to {reg.receiver_email} for {reg.symbol_number}",
                        registration_id=reg.id,
                        symbol_number=reg.symbol_number,
                    )
                else:
                    await _log_event(
                        session,
                        event_type="EMAIL_FAILED",
                        message=f"Failed to send email to {reg.receiver_email} for {reg.symbol_number}",
                        registration_id=reg.id,
                        symbol_number=reg.symbol_number,
                    )

            else:
                # Result not yet published
                await session.execute(
                    update(Registration)
                    .where(Registration.id == reg.id)
                    .values(
                        last_checked_at=now,
                        check_count=reg.check_count + 1,
                        last_error=None,
                    )
                )
                await _log_event(
                    session,
                    event_type="NOT_FOUND",
                    message=f"Result not yet published for {reg.symbol_number}. Total checks: {reg.check_count + 1}",
                    registration_id=reg.id,
                    symbol_number=reg.symbol_number,
                )

            await session.commit()

        except Exception as e:
            logger.error(f"Error processing registration {reg.id} ({reg.symbol_number}): {e}")
            try:
                await session.execute(
                    update(Registration)
                    .where(Registration.id == reg.id)
                    .values(
                        last_checked_at=datetime.now(timezone.utc),
                        check_count=reg.check_count + 1,
                        last_error=str(e)[:500],
                    )
                )
                await _log_event(
                    session,
                    event_type="ERROR",
                    message=f"Error checking {reg.symbol_number}: {str(e)[:300]}",
                    registration_id=reg.id,
                    symbol_number=reg.symbol_number,
                )
                await session.commit()
            except Exception as inner_e:
                logger.error(f"Could not log error to DB: {inner_e}")


# ---------------------------------------------------------------------------
# Monitoring loop
# ---------------------------------------------------------------------------

async def _run_monitoring_loop() -> None:
    """Infinite loop that checks all active registrations at each interval."""
    global _is_monitoring
    _is_monitoring = True
    interval = settings.MONITOR_INTERVAL_SECONDS
    logger.info(f"🚀 Monitoring loop started. Interval: {interval}s")

    while _is_monitoring:
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Registration).where(
                    Registration.is_active == True,
                    Registration.result_found == False,
                )
                result = await session.execute(stmt)
                active_regs = result.scalars().all()

            if not active_regs:
                logger.debug("No active registrations to check.")
            else:
                logger.info(f"🔍 Checking {len(active_regs)} active registration(s)...")
                # Process concurrently but with a small semaphore to avoid hammering portals
                semaphore = asyncio.Semaphore(3)

                async def _sem_process(reg):
                    async with semaphore:
                        await _process_registration(reg)

                await asyncio.gather(*[_sem_process(r) for r in active_regs])
                logger.info("✅ Check cycle complete.")

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")

        # Wait for next cycle
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break

    _is_monitoring = False
    logger.info("🛑 Monitoring loop stopped.")


# ---------------------------------------------------------------------------
# Public start/stop
# ---------------------------------------------------------------------------

def start_monitoring() -> bool:
    """Start the background monitoring loop. Returns True if started."""
    global _monitoring_task, _is_monitoring

    if _monitoring_task and not _monitoring_task.done():
        logger.info("Monitoring already running.")
        return False

    loop = asyncio.get_event_loop()
    _monitoring_task = loop.create_task(_run_monitoring_loop())
    logger.info("Monitoring task created.")
    return True


def stop_monitoring() -> bool:
    """Stop the background monitoring loop."""
    global _monitoring_task, _is_monitoring
    _is_monitoring = False

    if _monitoring_task and not _monitoring_task.done():
        _monitoring_task.cancel()
        logger.info("Monitoring task cancelled.")
        return True
    return False


def is_monitoring() -> bool:
    """Return True if monitoring is currently running."""
    global _monitoring_task, _is_monitoring
    return _is_monitoring and _monitoring_task is not None and not _monitoring_task.done()
