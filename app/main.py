from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers import ChatController
import asyncio
import websockets
import uvicorn

app = FastAPI(title="DnD AI Dungeon Master")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ChatController.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "DnD AI GM is running"}

async def chatbot(websocket, path):
    async for message in websocket:
        print(f"Received: {message}")
        await websocket.send(f"Sent: {message}")

async def main():
    async with websockets.serve(chatbot, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    print("Starting WebSocket server on ws://localhost:8765...")
    asyncio.run(main())
    uvicorn.run(app, host="0.0.0.0", port=8000)
