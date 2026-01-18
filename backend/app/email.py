import os
from typing import Optional
import resend
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "onboarding@resend.dev") # Default Resend testing email
        
        if self.api_key:
            resend.api_key = self.api_key
            print("EmailService: Resend Enabled")
        else:
            print("EmailService: Mock Mode (No RESEND_API_KEY)")

    async def send_provider_notification(self, provider_email: str, customer_name: str, booking_link: str):
        subject = "New booking awaiting approval"
        body = f"""
        Hello,

        You have a new booking request from {customer_name}.
        
        Please review it in your dashboard:
        {booking_link}

        Regards,
        WorkSlot
        """
        
        if self.api_key:
            try:
                r = resend.Emails.send({
                    "from": self.from_email,
                    "to": provider_email,
                    "subject": subject,
                    "text": body
                })
                print(f"EMAIL SENT (Resend) to {provider_email}: {r}")
            except Exception as e:
                print(f"EMAIL FAILURE (Resend) to {provider_email}: {e}")
        else:
            print(f"EMAIL MOCK to {provider_email}: {subject} | {body}")

    async def send_customer_update(self, customer_email: str, status: str, business_name: str, comment: Optional[str] = None):
        subject = f"Booking {status.capitalize()} - {business_name}"
        body = f"""
        Hello,
        
        Your booking with {business_name} has been {status}.
        """
        
        if comment:
            body += f"\nNote from provider: {comment}\n"
            
        body += "\nRegards,\nWorkSlot"

        if self.api_key:
            try:
                r = resend.Emails.send({
                    "from": self.from_email,
                    "to": customer_email,
                    "subject": subject,
                    "text": body
                })
                print(f"EMAIL SENT (Resend) to {customer_email}: {r}")
            except Exception as e:
                print(f"EMAIL FAILURE (Resend) to {customer_email}: {e}")
        else:
            print(f"EMAIL MOCK to {customer_email}: {subject} | {body}")

email_service = EmailService()
