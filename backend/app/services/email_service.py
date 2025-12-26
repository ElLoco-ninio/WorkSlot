"""Email service for sending notifications."""
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.console_mode = settings.EMAIL_CONSOLE_MODE
        
        # Initialize Jinja2 for email templates
        import os
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "email")
        if os.path.exists(template_dir):
            self.jinja_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            self.jinja_env = None
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        if self.console_mode:
            # Log email to console in development
            logger.info("=" * 60)
            logger.info(f"EMAIL TO: {to_email}")
            logger.info(f"SUBJECT: {subject}")
            logger.info("-" * 60)
            logger.info(text_content or html_content)
            logger.info("=" * 60)
            print("\n" + "=" * 60)
            print(f"📧 EMAIL TO: {to_email}")
            print(f"📋 SUBJECT: {subject}")
            print("-" * 60)
            print(text_content or html_content)
            print("=" * 60 + "\n")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send via SMTP
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _render_template(self, template_name: str, **context) -> str:
        """Render an email template."""
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template(template_name)
                return template.render(**context)
            except Exception:
                pass
        
        # Fallback to inline template
        return self._get_inline_template(template_name, **context)
    
    def _get_inline_template(self, template_name: str, **context) -> str:
        """Get inline template when file templates are not available."""
        templates = {
            "verification.html": self._verification_template,
            "booking_confirmed.html": self._booking_confirmed_template,
            "booking_declined.html": self._booking_declined_template,
            "new_booking.html": self._new_booking_template,
        }
        
        template_func = templates.get(template_name)
        if template_func:
            return template_func(**context)
        
        return f"<p>{context}</p>"
    
    def _verification_template(self, **ctx) -> str:
        """Email verification template."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Booking</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">Confirm Your Booking</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p>Hi {ctx.get('customer_name', 'there')},</p>
        <p>Please confirm your booking with <strong>{ctx.get('business_name', 'the provider')}</strong>:</p>
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
            <p style="margin: 0;"><strong>Date & Time:</strong> {ctx.get('booking_date', 'N/A')}</p>
        </div>
        <p style="text-align: center;">
            <a href="{ctx.get('verification_url', '#')}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                ✓ Confirm Booking
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">This link expires in 24 hours.</p>
        <p style="color: #666; font-size: 14px;">If you didn't request this booking, please ignore this email.</p>
    </div>
</body>
</html>
"""
    
    def _booking_confirmed_template(self, **ctx) -> str:
        """Booking confirmed template for customer."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Booking Confirmed</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">✓ Booking Confirmed!</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p>Hi {ctx.get('customer_name', 'there')},</p>
        <p>Great news! Your booking with <strong>{ctx.get('business_name', 'the provider')}</strong> has been confirmed.</p>
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #11998e;">
            <p style="margin: 0;"><strong>Date & Time:</strong> {ctx.get('booking_date', 'N/A')}</p>
        </div>
        <p>We look forward to seeing you!</p>
    </div>
</body>
</html>
"""
    
    def _booking_declined_template(self, **ctx) -> str:
        """Booking declined template for customer."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Booking Update</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">Booking Update</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p>Hi {ctx.get('customer_name', 'there')},</p>
        <p>Unfortunately, your booking with <strong>{ctx.get('business_name', 'the provider')}</strong> could not be confirmed.</p>
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #eb3349;">
            <p style="margin: 0;"><strong>Reason:</strong> {ctx.get('reason', 'The requested time slot is not available.')}</p>
        </div>
        <p>Please try booking a different time slot.</p>
    </div>
</body>
</html>
"""
    
    def _new_booking_template(self, **ctx) -> str:
        """New booking notification for provider."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>New Booking Request</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">📅 New Booking Request</h1>
    </div>
    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
        <p>Hi {ctx.get('provider_name', 'there')},</p>
        <p>You have a new booking request that needs your attention.</p>
        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
            <p><strong>Customer:</strong> {ctx.get('customer_name', 'N/A')}</p>
            <p><strong>Email:</strong> {ctx.get('customer_email', 'N/A')}</p>
            <p style="margin: 0;"><strong>Date & Time:</strong> {ctx.get('booking_date', 'N/A')}</p>
        </div>
        <p style="text-align: center;">
            <a href="{ctx.get('dashboard_url', '#')}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                View in Dashboard
            </a>
        </p>
    </div>
</body>
</html>
"""
    
    async def send_booking_verification(
        self,
        to_email: str,
        customer_name: str,
        business_name: str,
        booking_date: datetime,
        verification_token: str,
    ) -> bool:
        """Send booking verification email to customer."""
        verification_url = f"{settings.FRONTEND_URL}/verify-booking?token={verification_token}"
        
        html_content = self._render_template(
            "verification.html",
            customer_name=customer_name,
            business_name=business_name,
            booking_date=booking_date.strftime("%A, %B %d, %Y at %I:%M %p"),
            verification_url=verification_url,
        )
        
        text_content = f"""
Hi {customer_name},

Please confirm your booking with {business_name}.

Date & Time: {booking_date.strftime("%A, %B %d, %Y at %I:%M %p")}

Click here to confirm: {verification_url}

This link expires in 24 hours.
"""
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Confirm your booking with {business_name}",
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_new_booking_notification(
        self,
        to_email: str,
        provider_name: str,
        customer_name: str,
        customer_email: str,
        booking_date: datetime,
    ) -> bool:
        """Send new booking notification to provider."""
        dashboard_url = f"{settings.FRONTEND_URL}/bookings"
        
        html_content = self._render_template(
            "new_booking.html",
            provider_name=provider_name,
            customer_name=customer_name,
            customer_email=customer_email,
            booking_date=booking_date.strftime("%A, %B %d, %Y at %I:%M %p"),
            dashboard_url=dashboard_url,
        )
        
        text_content = f"""
Hi {provider_name},

You have a new booking request!

Customer: {customer_name}
Email: {customer_email}
Date & Time: {booking_date.strftime("%A, %B %d, %Y at %I:%M %p")}

View in dashboard: {dashboard_url}
"""
        
        return await self.send_email(
            to_email=to_email,
            subject=f"New booking from {customer_name}",
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_booking_confirmed_to_customer(
        self,
        to_email: str,
        customer_name: str,
        business_name: str,
        booking_date: datetime,
    ) -> bool:
        """Send booking confirmation email to customer."""
        html_content = self._render_template(
            "booking_confirmed.html",
            customer_name=customer_name,
            business_name=business_name,
            booking_date=booking_date.strftime("%A, %B %d, %Y at %I:%M %p"),
        )
        
        text_content = f"""
Hi {customer_name},

Great news! Your booking with {business_name} has been confirmed.

Date & Time: {booking_date.strftime("%A, %B %d, %Y at %I:%M %p")}

We look forward to seeing you!
"""
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Booking confirmed with {business_name}",
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_booking_declined_to_customer(
        self,
        to_email: str,
        customer_name: str,
        business_name: str,
        reason: str,
    ) -> bool:
        """Send booking declined email to customer."""
        html_content = self._render_template(
            "booking_declined.html",
            customer_name=customer_name,
            business_name=business_name,
            reason=reason,
        )
        
        text_content = f"""
Hi {customer_name},

Unfortunately, your booking with {business_name} could not be confirmed.

Reason: {reason}

Please try booking a different time slot.
"""
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Booking update from {business_name}",
            html_content=html_content,
            text_content=text_content,
        )

