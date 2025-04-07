# db/crud.py

from db.database import experts_db

def get_available_expert(language: str = None):
    fallback = None

    for expert in experts_db:
        if expert.get("available"):
            # Perfect match on language
            if language and language in expert.get("languages", []):
                return expert
            
            # Save this in case we need fallback
            if fallback is None:
                fallback = expert

    # If no language-specific match, return any available expert
    return fallback
