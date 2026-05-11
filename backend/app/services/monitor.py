import asyncio
import json
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.models.registration import Registration
from app.models.log import ActivityLog
from app.services.scraper import check_result_with_retry
from app.services.email_service import send_result_email

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def _log_event(session: AsyncSession, **kwargs):
    log = ActivityLog(**kwargs)
    session.add(log)
    await session.flush()

async def process_registration(reg: Registration):
    async with AsyncSessionLocal() as session:
        try:
            await _log_event(session, event_type="CHECK_STARTED", message=f"Checking {reg.symbol_number}", 
                           registration_id=reg.id, symbol_number=reg.symbol_number)

            result = await check_result_with_retry(reg.symbol_number, reg.date_of_birth)

            if result and result.found:
                result_json = json.dumps({
                    "name": result.name, "school": result.school, "gpa": result.gpa,
                    "grade": result.grade, "subjects": result.subjects, "source_url": result.source_url
                })

                await session.execute(update(Registration).where(Registration.id == reg.id).values(
                    result_found=True, result_data=result_json, last_checked_at=datetime.now(timezone.utc),
                    check_count=reg.check_count + 1
                ))

                await _log_event(session, event_type="RESULT_FOUND", message=f"Result found! GPA={result.gpa}",
                               registration_id=reg.id, symbol_number=reg.symbol_number, source_url=result.source_url)

                email_ok = await send_result_email(reg.receiver_email, result, reg.symbol_number)
                if email_ok:
                    await session.execute(update(Registration).where(Registration.id == reg.id).values(
                        email_sent=True, is_active=False
                    ))
                    await _log_event(session, event_type="EMAIL_SENT", message=f"Email sent to {reg.receiver_email}",
                                   registration_id=reg.id, symbol_number=reg.symbol_number)
            else:
                await session.execute(update(Registration).where(Registration.id == reg.id).values(
                    last_checked_at=datetime.now(timezone.utc), check_count=reg.check_count + 1
                ))
                await _log_event(session, event_type="NOT_FOUND", message=f"Not found yet", 
                               registration_id=reg.id, symbol_number=reg.symbol_number)

            await session.commit()
        except Exception as e:
            logger.error(f"Error processing {reg.symbol_number}: {e}")
            # Log error...

def start_monitoring():
    if scheduler.running:
        return False
    scheduler.add_job(monitoring_job, 'interval', seconds=settings.MONITOR_INTERVAL_SECONDS, id='see_monitor')
    scheduler.start()
    logger.info("✅ Background monitoring started")
    return True

async def monitoring_job():
    async with AsyncSessionLocal() as session:
        stmt = select(Registration).where(Registration.is_active == True, Registration.result_found == False)
        regs = (await session.execute(stmt)).scalars().all()
        if regs:
            await asyncio.gather(*(process_registration(r) for r in regs))

def stop_monitoring():
    if scheduler.running:
        scheduler.shutdown()
        return True
    return False