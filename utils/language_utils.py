# utils/language_utils.py

from services.openai_service import client

def detect_language(text: str) -> str:
    """Detect the language of the input text using GPT-4o-mini.
    Returns one of: "ENGLISH", "PIDGIN ENGLISH", or "IGBO"
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a language detection system. Your task is to determine if the given text is in ENGLISH, PIDGIN ENGLISH, or IGBO.
                    Rules:
                    1. Return ONLY one of these exact strings: "ENGLISH", "PIDGIN ENGLISH", or "IGBO"
                    2. PIDGIN ENGLISH includes Nigerian Pidgin with words like 'wetin', 'dey', 'abeg', 'una', etc.
                    3. IGBO includes Igbo language text with words like 'akwa', 'ahia', 'ụzọ', 'anyị', etc.
                    4. If unsure, default to "ENGLISH"
                    5. Do not include any explanation or additional text in your response"""
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.1,  # Low temperature for consistent results
            max_tokens=10  # We only need a short response
        )
        
        detected_language = response.choices[0].message.content.strip().upper()
        print(f"🔊 Detected language: {detected_language}")
        
        # Ensure we only return one of our three valid options
        if detected_language not in ["ENGLISH", "PIDGIN ENGLISH", "IGBO"]:
            return "ENGLISH"  # Default to English if we get an unexpected response
            
        return detected_language
        
    except Exception as e:
        print(f"⚠️ Error in language detection: {e}")
        return "ENGLISH"  # Default to English on error
