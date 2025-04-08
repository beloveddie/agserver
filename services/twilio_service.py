# services/twilio_service.py

from twilio.rest import Client
import os
from dotenv import load_dotenv
from datetime import datetime
from config import db

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

def send_sms_to_expert(expert: dict, user_question: str, user_phone: str, user_language: str = "English"):
    message = (
        f"AgServer Alert 🚜\n"
        f"Hi {expert['name']}, a farmer needs your help.\n"
        f"Query: {user_question[:100]}...\n"
        f"Language: {user_language}\n"
        f"Contact Farmer: {user_phone}"
    )

    try:
        twilio_client.messages.create(
            to=expert["phone"],
            from_=TWILIO_PHONE,
            body=message
        )
        print(f"✅ SMS sent to expert {expert['name']} at {expert['phone']}")

        # ✅ Log the SMS send in MongoDB
        try:
            db.sms_logs.insert_one({
                "to": expert["phone"],
                "expert_name": expert["name"],
                "user_phone": user_phone,
                "user_question": user_question,
                "language": user_language,
                "timestamp": datetime.utcnow(),
                "status": "sent"
            })
            print(f"📬 SMS log for {expert['name']} saved to MongoDB.")
        except Exception as log_err:
            print(f"⚠️ SMS sent, but failed to log to DB: {log_err}")

    except Exception as send_err:
        print(f"❌ Failed to send SMS to expert: {send_err}")
