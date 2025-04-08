# routers/sms.py
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from twilio.twiml.messaging_response import MessagingResponse

from services.openai_service import get_chat_response
from services.escalation_service import check_if_escalation_needed, route_to_expert
from services.twilio_service import send_sms_to_expert
from utils.language_utils import detect_language

router = APIRouter()

@router.post("/sms-incoming")
async def sms_incoming(request: Request, From: str = Form(...), Body: str = Form(...)):
    print(f"📩 Incoming SMS from {From}: {Body}")

    user_language = detect_language(Body)
    print(f"🈯 Detected language: {user_language}")

    # Use OpenAI to get a response
    reply = get_chat_response(Body)
    print(f"🤖 Assistant reply: {reply}")

    # Check if escalation is needed
    if check_if_escalation_needed(reply):
        print("🚨 Escalation detected for incoming SMS.")

        expert = route_to_expert(Body, user_language)
        if expert:
            print(f"👨🏾‍🌾 Routing SMS query to expert: {expert['name']} ({expert['phone']})")

            send_sms_to_expert(
                expert=expert,
                user_question=Body,
                user_phone=From,
                user_language=user_language
            )

            reply += f"\n📲 Please expect a call or SMS shortly from {expert['name']}."
            print(reply)
        else:
            print("⚠️ No expert available for escalation via SMS.")
            reply += "\nSorry, no available expert found at the moment. We'll get back to you soon."
            print(reply)

    else:
        print("✅ No escalation needed for SMS message.")

    # Create TwiML response
    twiml = MessagingResponse()
    twiml.message(reply)

    print(f"📤 Responding to user {From} via SMS.")
    return HTMLResponse(content=str(twiml), media_type="application/xml")
