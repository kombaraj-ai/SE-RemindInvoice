"""
Email delivery service powered by SendGrid.

All functions are sync internally and safe to call from async code.
The ``_send`` helper is the single integration point with SendGrid.

If SENDGRID_API_KEY is not configured the functions log a warning and
return ``False`` so the application continues to work in dev without email.
"""

import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, Header, Mail, MimeType, ReplyTo

from app.config import settings

logger = logging.getLogger(__name__)


def _html_wrap(body_html: str) -> str:
    """Wrap a partial HTML snippet in a complete, spam-filter-friendly document."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RemindInvoice</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#1a1a1a;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;padding:40px;border:1px solid #e5e7eb;">
          <tr>
            <td style="padding-bottom:24px;border-bottom:1px solid #e5e7eb;">
              <span style="font-size:20px;font-weight:700;color:#4F46E5;">RemindInvoice</span>
            </td>
          </tr>
          <tr>
            <td style="padding-top:24px;">
              {body_html}
            </td>
          </tr>
          <tr>
            <td style="padding-top:32px;border-top:1px solid #e5e7eb;font-size:12px;color:#9ca3af;">
              <p style="margin:4px 0;">You received this email because you have an outstanding invoice with one of our users.</p>
              <p style="margin:4px 0;">RemindInvoice — automated invoice reminders for freelancers.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _send(to_email: str, subject: str, html_content: str, plain_content: str) -> bool:
    """
    Send a transactional email via SendGrid with both HTML and plain-text parts.

    :returns: ``True`` if SendGrid accepted the message (2xx), else ``False``.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning(
            "SENDGRID_API_KEY not set — skipping email to %s (subject: %s)",
            to_email,
            subject,
        )
        return False

    try:
        message = Mail(
            from_email=(settings.FROM_EMAIL, settings.FROM_NAME),
            to_emails=to_email,
            subject=subject,
        )
        message.reply_to = ReplyTo(settings.FROM_EMAIL, settings.FROM_NAME)

        # Plain text first, then HTML — multipart/alternative ordering matters
        message.add_content(Content(MimeType.text, plain_content))
        message.add_content(Content(MimeType.html, _html_wrap(html_content)))

        # List-Unsubscribe headers — required by Gmail bulk sender policy (2024)
        message.add_header(Header(
            "List-Unsubscribe",
            f"<mailto:{settings.FROM_EMAIL}?subject=unsubscribe>",
        ))
        message.add_header(Header("List-Unsubscribe-Post", "List-Unsubscribe=One-Click"))

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(
            "Email sent to %s [subject=%r, status=%s]",
            to_email,
            subject,
            response.status_code,
        )
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


# ---------------------------------------------------------------------------
# High-level email helpers
# ---------------------------------------------------------------------------

def send_welcome_email(to_email: str, full_name: str) -> bool:
    name = full_name or "there"
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard"
    html = (
        f"<p>Hi {name},</p>"
        "<p>Welcome to <strong>RemindInvoice</strong>! "
        "Start creating professional invoices and automated payment reminders today.</p>"
        f'<p><a href="{dashboard_url}" style="background:#4F46E5;color:#fff;padding:10px 20px;'
        'border-radius:6px;text-decoration:none;display:inline-block;">Go to Dashboard</a></p>'
        "<p>– The RemindInvoice Team</p>"
    )
    plain = (
        f"Hi {name},\n\n"
        "Welcome to RemindInvoice! Start creating professional invoices and "
        "automated payment reminders today.\n\n"
        f"Go to your dashboard: {dashboard_url}\n\n"
        "– The RemindInvoice Team"
    )
    return _send(to_email, "Welcome to RemindInvoice", html, plain)


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    html = (
        "<p>We received a request to reset your RemindInvoice password.</p>"
        f'<p><a href="{reset_url}" style="background:#4F46E5;color:#fff;padding:10px 20px;'
        'border-radius:6px;text-decoration:none;display:inline-block;">Reset Password</a></p>'
        "<p>This link expires in <strong>1 hour</strong>. "
        "If you did not request a reset, you can safely ignore this email.</p>"
        "<p>– The RemindInvoice Team</p>"
    )
    plain = (
        "We received a request to reset your RemindInvoice password.\n\n"
        f"Reset your password: {reset_url}\n\n"
        "This link expires in 1 hour. If you did not request a reset, "
        "you can safely ignore this email.\n\n"
        "– The RemindInvoice Team"
    )
    return _send(to_email, "Reset your RemindInvoice password", html, plain)


def send_invoice_email(
    to_email: str,
    client_name: str,
    invoice_number: str,
    public_token: str,
    pdf_path: str | None = None,
) -> bool:
    view_url = f"{settings.FRONTEND_URL}/invoices/public/{public_token}"
    html = (
        f"<p>Hi {client_name},</p>"
        f"<p>Invoice <strong>{invoice_number}</strong> has been sent to you.</p>"
        f'<p><a href="{view_url}" style="background:#4F46E5;color:#fff;padding:10px 20px;'
        'border-radius:6px;text-decoration:none;display:inline-block;">View Invoice</a></p>'
        "<p>If you have any questions, please reply to this email.</p>"
        "<p>Thank you for your business!</p>"
    )
    plain = (
        f"Hi {client_name},\n\n"
        f"Invoice {invoice_number} has been sent to you.\n\n"
        f"View your invoice: {view_url}\n\n"
        "If you have any questions, please reply to this email.\n\n"
        "Thank you for your business!"
    )
    if pdf_path:
        logger.info(
            "PDF attachment requested for invoice %s but not yet implemented",
            invoice_number,
        )
    return _send(to_email, f"Invoice {invoice_number} from RemindInvoice", html, plain)


def send_reminder_email(
    to_email: str,
    client_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    public_token: str,
) -> bool:
    view_url = f"{settings.FRONTEND_URL}/invoices/public/{public_token}"
    html = (
        f"<p>Hi {client_name},</p>"
        f"<p>Invoice <strong>{invoice_number}</strong> for <strong>{amount}</strong> "
        f"is due on <strong>{due_date}</strong>.</p>"
        f'<p><a href="{view_url}" style="background:#4F46E5;color:#fff;padding:10px 20px;'
        'border-radius:6px;text-decoration:none;display:inline-block;">View &amp; Pay Invoice</a></p>'
        "<p>If you have already sent payment, please disregard this message.</p>"
        "<p>Thank you!</p>"
    )
    plain = (
        f"Hi {client_name},\n\n"
        f"Invoice {invoice_number} for {amount} is due on {due_date}.\n\n"
        f"View and pay your invoice: {view_url}\n\n"
        "If you have already sent payment, please disregard this message.\n\n"
        "Thank you!"
    )
    return _send(
        to_email,
        f"Invoice {invoice_number} — payment due {due_date}",
        html,
        plain,
    )
