from fastapi import APIRouter, HTTPException
from app.models.ChatRequest import ChatRequest
from app.services.OpenAPIService import OpenAIService

router = APIRouter(prefix="/chat", tags=["Chat"])

client = OpenAIService()

@router.post("/message")
async def send_message(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Missing 'message'")

    reply = client.chat([
        {"role": "system", "content": "You are a fun, enthusiastic, creative DnD 5e Dungeon Master"},
        {"role": "user", "content": request.message},
        {"role": "assistant", "content": request.assistantMessage},
        {"role": "user", "content": request.message}
    ])
    return {"reply": reply}

@router.post("/start")
async def send_message():
    reply = client.startGame()
    return {"reply": reply}