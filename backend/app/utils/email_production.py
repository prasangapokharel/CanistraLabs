"""Enhanced email service with support for multiple providers (SendGrid, AWS SES, Mailgun, Postmark)."""

import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import aiohttp
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """Supported email providers."""

    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    MAILGUN = "mailgun"
    POSTMARK = "postmark"
    SMTP = "smtp"  # Fallback to standard SMTP


class EmailSettings(BaseModel):
    """Email configuration settings."""

    provider: EmailProvider = EmailProvider.SENDGRID
    from_email: str = "noreply@canistra.com"
    from_name: str = "Canistra"

    # SendGrid
    sendgrid_api_key: Optional[str] = None

    # AWS SES
    aws_ses_region: Optional[str] = None
    aws_ses_access_key_id: Optional[str] = None
    aws_ses_secret_access_key: Optional[str] = None

    # Mailgun
    mailgun_api_key: Optional[str] = None
    mailgun_domain: Optional[str] = None

    # Postmark
    postmark_server_token: Optional[str] = None

    # Standard SMTP (fallback)
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False


class EmailProviderBase(ABC):
    """Abstract base class for email providers."""

    def __init__(self, settings: EmailSettings):
        self.settings = settings

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        pass


class SendGridProvider(EmailProviderBase):
    """SendGrid email provider."""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> bool:
        """Send email via SendGrid."""
        try:
            if not self.settings.sendgrid_api_key:
                logger.error("SendGrid API key not configured")
                return False

            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.settings.sendgrid_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "personalizations": [
                    {
                        "to": [{"email": to_email, "name": to_name or ""}],
                        "subject": subject,
                    }
                ],
                "from": {
                    "email": self.settings.from_email,
                    "name": self.settings.from_name,
                },
                "content": [
                    {"type": "text/plain", "value": text_body or subject},
                    {"type": "text/html", "value": html_body},
                ],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"Email sent via SendGrid to {to_email}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"SendGrid error: {error_text}")
                        return False

        except Exception as e:
            logger.error(f"SendGrid provider error: {str(e)}")
            return False


class MailgunProvider(EmailProviderBase):
    """Mailgun email provider."""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> bool:
        """Send email via Mailgun."""
        try:
            if not self.settings.mailgun_api_key or not self.settings.mailgun_domain:
                logger.error("Mailgun API key or domain not configured")
                return False

            url = f"https://api.mailgun.net/v3/{self.settings.mailgun_domain}/messages"
            auth = ("api", self.settings.mailgun_api_key)

            data = {
                "from": f"{self.settings.from_name} <{self.settings.from_email}>",
                "to": f"{to_name} <{to_email}>" if to_name else to_email,
                "subject": subject,
                "text": text_body or subject,
                "html": html_body,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, auth=auth) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Email sent via Mailgun to {to_email}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Mailgun error: {error_text}")
                        return False

        except Exception as e:
            logger.error(f"Mailgun provider error: {str(e)}")
            return False


class PostmarkProvider(EmailProviderBase):
    """Postmark email provider."""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> bool:
        """Send email via Postmark."""
        try:
            if not self.settings.postmark_server_token:
                logger.error("Postmark server token not configured")
                return False

            url = "https://api.postmarkapp.com/email"
            headers = {
                "X-Postmark-Server-Token": self.settings.postmark_server_token,
                "Content-Type": "application/json",
            }

            payload = {
                "From": f"{self.settings.from_name} <{self.settings.from_email}>",
                "To": f"{to_name} <{to_email}>" if to_name else to_email,
                "Subject": subject,
                "TextBody": text_body or subject,
                "HtmlBody": html_body,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Email sent via Postmark to {to_email}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Postmark error: {error_text}")
                        return False

        except Exception as e:
            logger.error(f"Postmark provider error: {str(e)}")
            return False


class ProductionEmailService:
    """Production-grade email service with multi-provider support."""

    def __init__(self, settings: Optional[EmailSettings] = None):
        """Initialize email service."""
        if settings is None:
            settings = self._load_settings_from_env()

        self.settings = settings
        self.provider = self._get_provider()

        # Load templates
        self.jinja_env = Environment(
            loader=FileSystemLoader("app/templates/email"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    @staticmethod
    def _load_settings_from_env() -> EmailSettings:
        """Load settings from environment variables."""
        provider = os.getenv("SMTP_PROVIDER", "sendgrid").lower()

        return EmailSettings(
            provider=EmailProvider(provider),
            from_email=os.getenv("SENDGRID_FROM_EMAIL", "noreply@canistra.com"),
            from_name=os.getenv("SENDGRID_FROM_NAME", "Canistra"),
            sendgrid_api_key=os.getenv("SENDGRID_API_KEY"),
            aws_ses_region=os.getenv("AWS_SES_REGION"),
            aws_ses_access_key_id=os.getenv("AWS_SES_ACCESS_KEY_ID"),
            aws_ses_secret_access_key=os.getenv("AWS_SES_SECRET_ACCESS_KEY"),
            mailgun_api_key=os.getenv("MAILGUN_API_KEY"),
            mailgun_domain=os.getenv("MAILGUN_DOMAIN"),
            postmark_server_token=os.getenv("POSTMARK_SERVER_TOKEN"),
        )

    def _get_provider(self) -> EmailProviderBase:
        """Get email provider instance based on configuration."""
        if self.settings.provider == EmailProvider.SENDGRID:
            return SendGridProvider(self.settings)
        elif self.settings.provider == EmailProvider.MAILGUN:
            return MailgunProvider(self.settings)
        elif self.settings.provider == EmailProvider.POSTMARK:
            return PostmarkProvider(self.settings)
        elif self.settings.provider == EmailProvider.AWS_SES:
            # AWS SES provider would require boto3, not implemented here
            logger.warning("AWS SES provider not fully implemented, falling back to SendGrid")
            return SendGridProvider(self.settings)
        else:
            logger.warning(f"Unknown provider {self.settings.provider}, using SendGrid")
            return SendGridProvider(self.settings)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        to_name: Optional[str] = None,
    ) -> bool:
        """Send an email using the configured provider."""
        return await self.provider.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            to_name=to_name,
        )

    async def send_verification_email(
        self,
        to_email: str,
        to_name: str,
        verification_token: str,
        expires_in_hours: int = 24,
    ) -> bool:
        """Send email verification email."""
        try:
            verification_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"

            template = self.jinja_env.get_template("email-verification.html")
            html_body = template.render(
                user_name=to_name,
                verification_link=verification_link,
                expires_in_hours=expires_in_hours,
                app_name="Canistra",
                support_email=self.settings.from_email,
            )

            text_body = f"""
Hi {to_name},

Welcome to Canistra! Please verify your email address to complete your registration.

Click the link below to verify your email:
{verification_link}

This link will expire in {expires_in_hours} hour(s).

Best regards,
The Canistra Team
            """.strip()

            return await self.send_email(
                to_email=to_email,
                subject="Verify Your Email - Canistra",
                html_body=html_body,
                text_body=text_body,
                to_name=to_name,
            )

        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return False

    async def send_password_reset_email(
        self,
        to_email: str,
        to_name: str,
        reset_token: str,
        expires_in_hours: int = 1,
    ) -> bool:
        """Send password reset email."""
        try:
            reset_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"

            template = self.jinja_env.get_template("password-reset.html")
            html_body = template.render(
                user_name=to_name,
                reset_link=reset_link,
                expires_in_hours=expires_in_hours,
                app_name="Canistra",
                support_email=self.settings.from_email,
            )

            text_body = f"""
Hi {to_name},

You requested a password reset for your Canistra account.

Click the link below to reset your password:
{reset_link}

This link will expire in {expires_in_hours} hour(s).

If you didn't request this password reset, please ignore this email.

Best regards,
The Canistra Team
            """.strip()

            return await self.send_email(
                to_email=to_email,
                subject="Reset Your Password - Canistra",
                html_body=html_body,
                text_body=text_body,
                to_name=to_name,
            )

        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False

    async def send_welcome_email(self, to_email: str, to_name: str) -> bool:
        """Send welcome email after successful verification."""
        try:
            template = self.jinja_env.get_template("welcome.html")
            html_body = template.render(
                user_name=to_name,
                dashboard_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard",
                app_name="Canistra",
                support_email=self.settings.from_email,
            )

            text_body = f"""
Hi {to_name},

Welcome to Canistra! Your email has been verified and you're ready to deploy your first project.

Get started: {os.getenv("FRONTEND_URL", "http://localhost:3000")}/dashboard

Best regards,
The Canistra Team
            """.strip()

            return await self.send_email(
                to_email=to_email,
                subject="Welcome to Canistra!",
                html_body=html_body,
                text_body=text_body,
                to_name=to_name,
            )

        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False


# Global email service instance
email_service = ProductionEmailService()
