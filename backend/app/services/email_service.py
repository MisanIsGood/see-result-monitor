"""
Email service – sends SEE result notifications via Gmail SMTP.
"""
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings
from app.services.scraper import SEEResult

logger = logging.getLogger(__name__)


def _build_email_html(result: SEEResult, symbol: str) -> str:
    """Build a nice HTML email body for the result notification."""
    subject_rows = ""
    if result.subjects:
        for subj, grade in result.subjects.items():
            subject_rows += f"""
            <tr>
                <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;">{subj}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1a56db;">{grade}</td>
            </tr>"""

    subjects_table = ""
    if subject_rows:
        subjects_table = f"""
        <table style="width:100%;border-collapse:collapse;margin-top:16px;">
            <thead>
                <tr style="background:#f8fafc;">
                    <th style="padding:10px 12px;text-align:left;font-size:13px;color:#6b7280;">Subject</th>
                    <th style="padding:10px 12px;text-align:left;font-size:13px;color:#6b7280;">Grade</th>
                </tr>
            </thead>
            <tbody>{subject_rows}</tbody>
        </table>"""

    name_row = f"<p style='margin:4px 0;color:#374151;'><strong>Name:</strong> {result.name}</p>" if result.name else ""
    school_row = f"<p style='margin:4px 0;color:#374151;'><strong>School:</strong> {result.school}</p>" if result.school else ""
    district_row = f"<p style='margin:4px 0;color:#374151;'><strong>District:</strong> {result.district}</p>" if result.district else ""

    gpa_badge = ""
    if result.gpa:
        gpa_badge = f"""
        <div style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
                    color:white;padding:12px 24px;border-radius:12px;margin:16px 0;font-size:24px;font-weight:700;">
            GPA: {result.gpa}
        </div>"""

    grade_badge = ""
    if result.grade:
        grade_badge = f"""
        <div style="display:inline-block;background:#dcfce7;color:#166534;
                    padding:8px 20px;border-radius:8px;margin:8px 0;font-size:18px;font-weight:600;">
            Grade: {result.grade}
        </div>"""

    status_color = "#dcfce7" if "pass" in result.result_status.lower() else "#fef3c7"
    status_text_color = "#166534" if "pass" in result.result_status.lower() else "#92400e"

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:600px;margin:32px auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1a56db,#0e9f6e);padding:32px;text-align:center;">
      <h1 style="color:white;margin:0;font-size:24px;font-weight:700;">🎓 SEE Result Published!</h1>
      <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:15px;">
        Your Secondary Education Examination result is now available.
      </p>
    </div>

    <!-- Body -->
    <div style="padding:32px;">

      <!-- Status badge -->
      <div style="background:{status_color};color:{status_text_color};padding:10px 16px;
                  border-radius:8px;font-weight:600;font-size:15px;margin-bottom:20px;text-align:center;">
        Status: {result.result_status or "Result Available"}
      </div>

      <!-- Student info -->
      <div style="background:#f8fafc;border-radius:10px;padding:16px 20px;margin-bottom:16px;">
        <p style="margin:4px 0;color:#374151;"><strong>Symbol Number:</strong> {symbol}</p>
        {name_row}
        {school_row}
        {district_row}
        <p style="margin:4px 0;color:#374151;"><strong>Source:</strong> {result.source_url}</p>
      </div>

      <!-- GPA & Grade -->
      <div style="text-align:center;">
        {gpa_badge}
        <br>
        {grade_badge}
      </div>

      <!-- Subject table -->
      {subjects_table}

      <!-- Note -->
      <div style="margin-top:24px;padding:16px;background:#eff6ff;border-radius:8px;border-left:4px solid #1a56db;">
        <p style="margin:0;color:#1e40af;font-size:13px;">
          💡 For your official result with marksheet, visit
          <a href="https://see.ntc.net.np/" style="color:#1a56db;">see.ntc.net.np</a> or
          <a href="https://result.neb.gov.np/" style="color:#1a56db;">result.neb.gov.np</a>.
          Enter your symbol number and date of birth.
        </p>
      </div>
    </div>

    <!-- Footer -->
    <div style="background:#f8fafc;padding:20px 32px;text-align:center;border-top:1px solid #e5e7eb;">
      <p style="margin:0;color:#9ca3af;font-size:12px;">
        This notification was sent by SEE Result Monitor &bull;
        You signed up to receive alerts for symbol <strong>{symbol}</strong>.
      </p>
    </div>
  </div>
</body>
</html>"""


async def send_result_email(to_email: str, result: SEEResult, symbol_number: str) -> bool:
    """
    Send a formatted result notification email via Gmail SMTP.
    Returns True on success, False on failure.
    """
    if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
        logger.error("Gmail credentials not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎓 SEE Result Found! Symbol: {symbol_number} – GPA: {result.gpa or 'N/A'}"
    msg["From"] = f"SEE Result Monitor <{settings.GMAIL_USER}>"
    msg["To"] = to_email

    # Plain text fallback
    plain = (
        f"SEE Result Published!\n\n"
        f"Symbol Number: {symbol_number}\n"
        f"Name: {result.name or 'N/A'}\n"
        f"GPA: {result.gpa or 'N/A'}\n"
        f"Grade: {result.grade or 'N/A'}\n"
        f"Status: {result.result_status or 'Result Available'}\n"
        f"Source: {result.source_url}\n\n"
        f"Visit see.ntc.net.np for your official marksheet."
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(_build_email_html(result, symbol_number), "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=settings.GMAIL_USER,
            password=settings.GMAIL_APP_PASSWORD,
            timeout=30,
        )
        logger.info(f"📧 Email sent successfully to {to_email} for symbol {symbol_number}")
        return True
    except aiosmtplib.SMTPAuthenticationError:
        logger.error("Gmail SMTP authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD.")
        return False
    except aiosmtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {e}")
        return False
