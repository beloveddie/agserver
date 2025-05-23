# services/escalation_service.py

from db.crud import get_available_expert
from services.openai_service import client

def check_if_escalation_needed(ai_response: str = "", user_message: str = "") -> bool:
    """Use GPT-4o-mini to determine if an escalation to a human expert is needed.
    Args:
        ai_response: The AI's response to the user
        user_message: The user's original message (optional)
    Returns:
        bool: True if escalation is needed, False otherwise
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an escalation detection system for AgServer, an agricultural assistant.
                    Your task is to determine if a conversation should be escalated to a human expert.
                    
                    ESCALATION TRIGGERS:
                    1. User explicitly requests a human expert
                    2. Question is beyond AI's agricultural knowledge
                    3. Complex technical issues requiring hands-on expertise
                    
                    Return ONLY "YES" or "NO" based on these rules:
                    - Return "YES" if any trigger is met
                    - Return "NO" if no triggers are met
                    - Do not include any explanation or additional text
                    - Be conservative - only escalate when clearly needed"""
                },
                {
                    "role": "user",
                    "content": f"AI Response: {ai_response}\nUser Message: {user_message}"
                }
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=10  # We only need a short response
        )
        
        decision = response.choices[0].message.content.strip().upper()
        return decision == "YES"
        
    except Exception as e:
        print(f"⚠️ Error in escalation detection: {e}")
        # Fallback to basic trigger phrase detection
        trigger_phrases = [
            "connecting to human expert now",
            "connecting you to a human expert now",
        ]
        return any(p in ai_response.lower() for p in trigger_phrases)


def route_to_expert(user_message: str, user_language: str) -> dict:
    # In future: match based on crop, region, etc.
    expert = get_available_expert(language=user_language)
    # log the expert that was matched to the user query
    if expert and user_language not in expert["languages"]:
        print(f"⚠️ No expert available for '{user_language}', falling back to: {expert['name']}")

    if expert:
        print(f"Routing to expert: {expert['name']} ({expert['phone']})")
        return expert
    return None
