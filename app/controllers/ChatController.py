from fastapi import APIRouter, HTTPException
from app.models.ChatRequest import ChatRequest
from app.services.OpenAPIService import openai_service
from app.services.AzureSpeechService import speech_service
import base64

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message")
async def send_message(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Missing 'message'")
    
    # Get AI response
    reply = await openai_service.chat(request.message, "user-123")
    
    # Try to generate audio
    audio_base64 = None
    if speech_service.is_initialized:
        try:
            audio_bytes = await speech_service.text_to_speech(reply)
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            print(f"⚠️  Failed to generate speech: {e}")
            # Continue without audio if speech generation fails
    
    return {
        "reply": reply,
        "audio": audio_base64,
        "audio_available": audio_base64 is not None
    }


@router.post("/start")
async def start_game():
    reply = await openai_service.chat("Bắt đầu trò chơi", "user-123")
    return {"reply": reply}
