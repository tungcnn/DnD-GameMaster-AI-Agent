from fastapi import APIRouter, HTTPException
from app.models.ChatRequest import ChatRequest
from app.services.OpenAPIService import openai_service
from app.services.WebsocketService import ws_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message")
async def send_message(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Missing 'message'")
    reply = await openai_service.chat(request.message, "user-123")

    # Send message to server
    await ws_service.client_send_message(reply)
        
    return {"reply": reply}


@router.post("/start")
async def start_game():
    reply = await openai_service.chat("Bắt đầu trò chơi", "user-123")

    # Send message to server
    await ws_service.client_send_message(reply)

    return {"reply": reply}
