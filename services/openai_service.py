# services/openai_service.py

import json
import openai
from openai import OpenAI
from config import OPENAI_API_KEY, SYSTEM_MESSAGE, VOICE

openai.api_key = OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

async def initialize_session(openai_ws, user_language="English"):
    """Initialize a streaming conversation session with GPT-4o."""
    # Get language-specific instructions
    language_instructions = get_language_instructions(user_language)
    
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": f"{SYSTEM_MESSAGE}\n\n{language_instructions}",
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    print('>>> Sending session update')
    await openai_ws.send(json.dumps(session_update))

    # Enable this if you want the AI to speak first
    await send_initial_conversation_item(openai_ws, user_language)

def get_language_instructions(language: str) -> str:
    """Get language-specific instructions for the AI."""
    instructions = {
        "PIDGIN ENGLISH": """
        LANGUAGE INSTRUCTIONS:
        - Speak in Nigerian Pidgin English
        - Use common Pidgin expressions and phrases
        - Keep responses simple and direct
        - Use local farming terms in Pidgin
        - Be friendly and conversational
        """,
        "IGBO": """
        LANGUAGE INSTRUCTIONS:
        - Speak in Igbo language
        - Use proper Igbo farming terminology
        - Keep responses clear and concise
        - Use traditional Igbo farming expressions
        - Be respectful and culturally appropriate
        """,
        "English": """
        LANGUAGE INSTRUCTIONS:
        - Speak in clear, simple English
        - Use standard farming terminology
        - Keep responses straightforward
        - Be professional yet friendly
        - Use proper English grammar
        """
    }
    return instructions.get(language, instructions["English"])

async def send_initial_conversation_item(openai_ws, user_language="English"):
    """Send a greeting message from the assistant when the call starts."""
    greetings = {
        "PIDGIN ENGLISH": "Ah! Hello farmer, na Agserver be this—your trusted AI helper for farm. You fit ask me anything about your crops, animals, or farm wahala.",
        "IGBO": "Ndewo! M bụ Agserver—onye enyemaka gị n'ugbo. Biko jụọ m ihe ọ bụla gbasara ihe ọkụkụ, anụ ụlọ, ma ọ bụ ọrụ ugbo gị.",
        "English": "Ah! Hello farmer, this is Agserver—your trusted AI helper for the farm. Feel free to ask me anything about your crops, animals, or farm matters."
    }
    
    greeting = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"Greet the user with '{greetings.get(user_language, greetings['English'])}'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(greeting))
    await openai_ws.send(json.dumps({"type": "response.create"}))
    print(">>> Sent initial assistant greeting")


def get_chat_response(user_message: str, user_language: str = "ENGLISH") -> str:
    """Get a plain text response from GPT-4o (used for SMS).
    Args:
        user_message: The message from the user
        user_language: The detected language ("ENGLISH", "PIDGIN ENGLISH", or "IGBO")
    """
    # Add language-specific instructions to the system message
    language_instructions = {
        "ENGLISH": """
        Respond in clear, professional English.
        FORMATTING RULES:
        - Use plain text only, no markdown
        - Use CAPS for emphasis instead of **bold**
        - Use dashes (-) for bullet points
        - Keep paragraphs short (2-3 lines max)
        - Use numbers (1. 2. 3.) for steps
        - Use simple line breaks for separation
        """,
        "PIDGIN ENGLISH": """
        Respond in Nigerian Pidgin English, using common phrases like 'wetin', 'dey', 'abeg', 'una', etc.
        FORMATTING RULES:
        - Use plain text only, no markdown
        - Use CAPS for emphasis instead of **bold**
        - Use dashes (-) for bullet points
        - Keep paragraphs short (2-3 lines max)
        - Use numbers (1. 2. 3.) for steps
        - Use simple line breaks for separation
        """,
        "IGBO": """
        Respond in Igbo language, using proper Igbo grammar and vocabulary.
        FORMATTING RULES:
        - Use plain text only, no markdown
        - Use CAPS for emphasis instead of **bold**
        - Use dashes (-) for bullet points
        - Keep paragraphs short (2-3 lines max)
        - Use numbers (1. 2. 3.) for steps
        - Use simple line breaks for separation
        """
    }
    
    language_instruction = language_instructions.get(user_language, language_instructions["ENGLISH"])
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"{SYSTEM_MESSAGE}\n\n{language_instruction}"},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
    )
    return f"{response.choices[0].message.content}"
