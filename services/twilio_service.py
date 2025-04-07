# services/twilio_service.py

from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

def send_sms_to_expert(expert: dict, user_question: str):
    message = (
        f"AgServer Alert 🚜\n"
        f"Hi {expert['name']}, a farmer needs help.\n"
        f"Query: {user_question[:100]}...\n"
        f"Please call back or reply if needed."
    )

    try:
        twilio_client.messages.create(
            to=expert["phone"],
            from_=TWILIO_PHONE,
            body=message
        )
        print(f"✅ SMS sent to expert {expert['name']} at {expert['phone']}")
    except Exception as e:
        print(f"❌ Failed to send SMS to expert: {e}")
