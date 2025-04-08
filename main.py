# main.py
from fastapi import FastAPI
from config import PORT, OPENAI_API_KEY, db
from routers import voice, sms
from pymongo.errors import ConnectionFailure
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        db.command("ping")
        print("✅ MongoDB connection successful.")
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise RuntimeError("MongoDB is not available. Startup aborted.")
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

if not OPENAI_API_KEY:
    raise ValueError("Missing the OpenAI API key. Please set it in the .env file.")

# Include routers
app.include_router(voice.router)
app.include_router(sms.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
