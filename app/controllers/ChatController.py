from fastapi import APIRouter, HTTPException
from app.models.ChatRequest import ChatRequest
from app.services.OpenAPIService import openai_service
import asyncio
import websockets

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message")
async def send_message(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Missing 'message'")
    reply = openai_service.chat(request.message, "user-123")

    # Send to server
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send(reply)

    return {"reply": reply}


@router.post("/start")
async def start_game():
    #reply = await openai_service.chat("Bắt đầu trò chơi", "user-123")
    reply = "Bắt đầu trò chơi"

    # Send to server
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send(reply)

    return {"reply": reply}
