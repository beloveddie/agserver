# main.py
from fastapi import FastAPI
from config import PORT, OPENAI_API_KEY
from routers import voice, sms

app = FastAPI()

if not OPENAI_API_KEY:
    raise ValueError("Missing the OpenAI API key. Please set it in the .env file.")

app.include_router(voice.router)
app.include_router(sms.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
