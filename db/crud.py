# db/crud.py

from config import db

def get_available_expert(language: str = None):
    try:
        query = {"available": True}
        experts = list(db.experts.find(query))

        fallback = None
        for expert in experts:
            if language and language in expert.get("languages", []):
                return expert
            if fallback is None:
                fallback = expert

        return fallback

    except Exception as e:
        print(f"❌ Error fetching expert from DB: {e}")
        return None
