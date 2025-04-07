# services/escalation_service.py

from db.crud import get_available_expert

def check_if_escalation_needed(ai_response: str, user_message: str) -> bool:
    trigger_phrases = [
        "let me connect you", "do you want to speak to a human",
        "connecting you now", "talk to a farming expert",
        "i recommend speaking with a human"
    ]
    user_triggers = [
        "i want to talk to a human", "connect me to an expert",
        "can i talk to someone", "talk to person", "human being", "call someone"
    ]
    return (
        any(p in ai_response.lower() for p in trigger_phrases) or
        any(p in user_message.lower() for p in user_triggers)
    )


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
