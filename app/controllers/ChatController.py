from fastapi import APIRouter, HTTPException
from app.DTOs.GameState import GameState
from app.models.ChatRequest import ChatRequest
from app.services.OpenAPIService import OpenAIService

router = APIRouter(prefix="/chat", tags=["Chat"])

openai_service = OpenAIService()


@router.post("/message")
async def send_message(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Missing 'message'")
    reply = openai_service.chat(GameState(input=request.message), "user-123")
    return {"reply": reply}


# @router.post("/start")
# async def start_game():
#     reply = openai_service.startGame("user-123")
#     return {"reply": reply}
