from pydantic import BaseModel
from typing import List

class Expert(BaseModel):
    id: int
    name: str
    phone: str
    specialty: str
    languages: List[str]  # e.g., ["English", "Pidgin"]
    available: bool = True
