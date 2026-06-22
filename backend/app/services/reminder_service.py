"""Appointment reminder service — sends notifications for upcoming appointments."""

from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.services.notification_service import notify


async def send_appointment_reminders(
    db: AsyncSession,
    hours_before: int = 24,
):
    """Find upcoming confirmed appointments and send reminder notifications.

    Call this from a cron/scheduler (e.g. every hour).
    Returns the count of reminders sent.
    """
    now = datetime.now(timezone.utc)
    window_start = now
    window_end = now + timedelta(hours=hours_before)

    # Find confirmed appointments in the reminder window
    # We combine date + time for comparison
    result = await db.execute(
        select(Appointment).where(
            Appointment.status == AppointmentStatus.CONFIRMED,
            Appointment.date >= window_start.date(),
            Appointment.reminder_sent == False,
        )
    )
    appointments = result.scalars().all()

    sent = 0
    for appt in appointments:
        # Combine date + time to get appointment datetime
        appt_dt = datetime.combine(appt.date, appt.time, tzinfo=timezone.utc)
        if window_start <= appt_dt <= window_end:
            # Send to patient
            await notify(
                db,
                user_id=appt.patient_id,
                title="تذكير بالموعد",
                body=f"لديك موعد قادم خلال {hours_before} ساعة",
                notification_type="appointment",
                data={"appointment_id": str(appt.id), "action": "reminder"},
            )
            # Send to doctor
            await notify(
                db,
                user_id=appt.doctor_id,
                title="تذكير بالموعد",
                body=f"لديك موعد قادم خلال {hours_before} ساعة",
                notification_type="appointment",
                data={"appointment_id": str(appt.id), "action": "reminder"},
            )
            appt.reminder_sent = True
            sent += 1

    await db.flush()
    return sent
