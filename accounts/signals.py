from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from accounts.models import OTP 
import random
from django.utils import timezone
from datetime import timedelta
import requests
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")


def generate_otp():
    otp = random.randint(100000, 999999)
    return otp

User = get_user_model()

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        instance.is_active = True
        instance.save()

        otp = generate_otp()
        print(otp)

        expiry_date = timezone.now() + timedelta(minutes=10)

        OTP.objects.create(
            otp=otp,
            user=instance,
            expiry_date=expiry_date
        )

        data = {
            "personalizations": [{
                "to": [{"email": instance.email}],
                "subject": "Welcome! Verify your account"
            }],
            "from": {"email": FROM_EMAIL},
            "content": [{
                "type": "text/html",
                "value": f"<p>Hello {instance.full_name},</p><p>Your verification OTP is <strong>{otp}</strong>. It will expire in 10 minutes.</p>"
            }]
        }

        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data
        )

        print("Status:", response.status_code)
        print("Response:", response.text)

