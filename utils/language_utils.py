# utils/language_utils.py

import re

def detect_language(text: str) -> str:
    """Rudimentary language detector based on keywords."""
    text = text.lower()

    # Igbo examples
    igbo_keywords = ["akwa", "ahia", "ụzọ", "anyị", "mma", "nna", "anyị", "ụtụtụ"]
    if any(word in text for word in igbo_keywords):
        return "Igbo"

    # Pidgin examples
    pidgin_keywords = ["wetin", "dey", "abeg", "una", "go fit", "make we", "waka", "na him", "no worry"]
    if any(word in text for word in pidgin_keywords):
        return "Pidgin"

    # Default fallback
    return "English"
