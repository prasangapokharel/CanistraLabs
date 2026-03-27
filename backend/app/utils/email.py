"""Email service utilities for sending emails."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class EmailSettings(BaseModel):
    """Email configuration settings."""

    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    from_email: str = "noreply@icphosting.com"
    from_name: str = "ICP Hosting Platform"


email_settings = EmailSettings(
    smtp_host=getattr(settings, "email_smtp_host", "localhost"),
    smtp_port=getattr(settings, "email_smtp_port", 587),
    smtp_username=getattr(settings, "email_smtp_username", ""),
    smtp_password=getattr(settings, "email_smtp_password", ""),
    smtp_use_tls=getattr(settings, "email_smtp_use_tls", True),
    smtp_use_ssl=getattr(settings, "email_smtp_use_ssl", False),
    from_email=getattr(settings, "email_from_email", "noreply@icphosting.com"),
    from_name=getattr(settings, "email_from_name", "ICP Hosting Platform"),
)


class EmailService:
    """Service for sending emails with HTML templates."""

    def __init__(self):
        """Initialize email service with template environment."""
        self.jinja_env = Environment(
            loader=FileSystemLoader("app/templates/email"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> bool:
        """Send an email using SMTP."""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{email_settings.from_name} <{email_settings.from_email}>"
            message["To"] = f"{to_name} <{to_email}>" if to_name else to_email

            # Add text part if provided
            if text_body:
                text_part = MIMEText(text_body, "plain")
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Send email
            if email_settings.smtp_use_ssl:
                server = smtplib.SMTP_SSL(email_settings.smtp_host, email_settings.smtp_port)
            else:
                server = smtplib.SMTP(email_settings.smtp_host, email_settings.smtp_port)
                if email_settings.smtp_use_tls:
                    server.starttls()

            if email_settings.smtp_username and email_settings.smtp_password:
                server.login(email_settings.smtp_username, email_settings.smtp_password)

            server.send_message(message)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_password_reset_email(
        self, to_email: str, to_name: str, reset_token: str, expires_in_hours: int = 1
    ) -> bool:
        """Send password reset email."""
        try:
            # Generate reset link
            reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"

            # Render HTML template
            template = self.jinja_env.get_template("password_reset.html")
            html_body = template.render(
                user_name=to_name,
                reset_link=reset_link,
                expires_in_hours=expires_in_hours,
                app_name=settings.app_name,
                support_email=email_settings.from_email,
            )

            # Create text version
            text_body = f"""
Hi {to_name},

You requested a password reset for your {settings.app_name} account.

Click the link below to reset your password:
{reset_link}

This link will expire in {expires_in_hours} hour(s).

If you didn't request this password reset, please ignore this email.

Best regards,
The {settings.app_name} Team
            """.strip()

            subject = f"Reset your {settings.app_name} password"

            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                to_name=to_name,
            )

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            return False

    async def send_password_reset_confirmation_email(self, to_email: str, to_name: str) -> bool:
        """Send password reset confirmation email."""
        try:
            # Render HTML template
            template = self.jinja_env.get_template("password_reset_confirmation.html")
            html_body = template.render(
                user_name=to_name,
                app_name=settings.app_name,
                support_email=email_settings.from_email,
                login_url=f"{settings.frontend_url}/login",
            )

            # Create text version
            text_body = f"""
Hi {to_name},

Your password has been successfully reset for your {settings.app_name} account.

You can now log in with your new password at: {settings.frontend_url}/login

If you didn't reset your password, please contact our support team immediately at {email_settings.from_email}.

Best regards,
The {settings.app_name} Team
            """.strip()

            subject = f"Your {settings.app_name} password has been reset"

            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                to_name=to_name,
            )

        except Exception as e:
            logger.error(
                f"Failed to send password reset confirmation email to {to_email}: {str(e)}"
            )
            return False


# Global email service instance
email_service = EmailService()
