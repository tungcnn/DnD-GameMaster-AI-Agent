from contextlib import asynccontextmanager
from sqlite3 import OperationalError

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.controllers import ChatController
from app.services.OpenAPIService import openai_service
from app.services.SqliteService import sqlite_service
import websockets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    try:
        await sqlite_service.init()
        openai_service.init_openai_service()
        print("Game master initialized")
    except OperationalError as e:
        print(e)

    yield  # <--- App runs here

    # --- Shutdown ---
    print("🛑 App closed")


app = FastAPI(title="DnD AI Dungeon Master", lifespan=lifespan)

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
