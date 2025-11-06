from contextlib import asynccontextmanager
from sqlite3 import OperationalError

import uvicorn
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
from sqlite3 import OperationalError

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.controllers import ChatController
from app.services.ChatService import openai_service
from app.services.SqliteService import sqlite_service
from app.services.WebsocketService import ws_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    try:
        await sqlite_service.init()
        if openai_service.dnd_graph:
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_obj = await ws_service.handle_connect(websocket)
    await ws_service.handle_receive(websocket, client_obj, openai_service)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_obj = await ws_service.handle_connect(websocket)
    await ws_service.handle_receive(websocket, client_obj, openai_service)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)