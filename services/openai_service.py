# services/openai_service.py

import json
import openai
from openai import OpenAI
from config import OPENAI_API_KEY, SYSTEM_MESSAGE, VOICE

openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

async def initialize_session(openai_ws):
    """Initialize a streaming conversation session with GPT-4o."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    print('>>> Sending session update')
    await openai_ws.send(json.dumps(session_update))

    # Enable this if you want the AI to speak first
    await send_initial_conversation_item(openai_ws)


async def send_initial_conversation_item(openai_ws):
    """Send a greeting message from the assistant when the call starts."""
    greeting = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Greet the user with 'Ah! Hello farmer, this is Agserver—your trusted AI helper for the farm. Feel free to ask me anything about your crops, animals, or farm wahala.'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(greeting))
    await openai_ws.send(json.dumps({"type": "response.create"}))
    print(">>> Sent initial assistant greeting")


def get_chat_response(user_message: str) -> str:
    """Get a plain text response from GPT-4o (used for SMS)."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
    )
    return f"{response.choices[0].message.content}"
