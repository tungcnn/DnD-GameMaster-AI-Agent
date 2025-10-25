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
    reply = await openai_service.chat(request.message, "user-123")

    # Send to server and received
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        await websocket.send(reply)
        print(f"Client sent: {reply}")
        response = await websocket.recv()
        print("Client received:", response)
        await asyncio.sleep(3)  # keep connect for test
        
    return {"reply": reply}


@router.post("/start")
async def start_game():
    reply = await openai_service.chat("Bắt đầu trò chơi", "user-123")

    # Send to server and received
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        await websocket.send(reply)
        print(f"Client sent: {reply}")
        response = await websocket.recv()
        print("Client received:", response)
        await asyncio.sleep(3)  # keep connect for test

    return {"reply": reply}
