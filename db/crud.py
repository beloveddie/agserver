# db/crud.py

from db.database import experts_db

def get_available_expert(language: str = None):
    for expert in experts_db:
        if expert.get("available"):
            if not language or language in expert.get("languages", []):
                return expert
    return None
