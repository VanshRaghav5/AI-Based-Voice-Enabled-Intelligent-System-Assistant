from fastapi import FastAPI
from backend.api.voice import router as voice_router

app = FastAPI(title="OmniAssist AI Backend")

app.include_router(voice_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "OmniAssist AI backend is running"}
