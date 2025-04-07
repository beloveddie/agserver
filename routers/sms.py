# routers/sms.py
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from twilio.twiml.messaging_response import MessagingResponse

from services.openai_service import get_chat_response
from services.escalation_service import check_if_escalation_needed, route_to_expert

router = APIRouter()

@router.post("/sms-incoming")
async def sms_incoming(request: Request, From: str = Form(...), Body: str = Form(...)):
    print(f"📩 Incoming SMS from {From}: {Body}")

    # Use OpenAI to get a response
    reply = get_chat_response(Body)

    # Check if escalation is needed
    if check_if_escalation_needed(reply):
        expert = route_to_expert(Body)
        if expert:
            reply += f"\nPlease expect a call or SMS shortly from {expert['name']}."

    # Create TwiML response
    twiml = MessagingResponse()
    twiml.message(reply)

    return HTMLResponse(content=str(twiml), media_type="application/xml")
