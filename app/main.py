from contextlib import asynccontextmanager
from sqlite3 import OperationalError

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.controllers import ChatController
from app.services.OpenAPIService import openai_service
from app.services.SqliteService import sqlite_service
import websockets
import json

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

connected_clients = set()
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_id = hex(id(websocket))
    connected_clients.add(websocket)
    print(f"Client connected: {(connected_clients)}")

    # Khi client kết nối bắn list các client đang conected để FE load
    for client in connected_clients:
        try:
            await client.send_text(f"{connected_clients}")
        except Exception as e:
            print("Send error:", e)    

    try:
        while True:
            # Chỉ gửi đúng 1 lần mỗi khi nhận được message
            data_text = await websocket.receive_text()
            print(f"Server received: {data_text}")

            # Convert JSON dạng {"user": "string", "type": 0, "message": "string"}
            try:
                data = json.loads(data_text)
            except Exception as e:
                # Gửi thông báo lỗi về cho client vừa gửi
                error_msg = f"JSON parse error: {str(e)}. Message must be like: {{'user': str, 'type': str, 'message': str}} (type: READY/CHAT)"
                try:
                    await websocket.send_text(error_msg)
                except Exception as err:
                    print("Send error to client:", err)
                continue  # bỏ qua broadcast

            user = data.get("user", "Unknown")
            msg_type = data.get("type", "Unknown")
            message = data.get("message", "")

            # Xử lý theo từng type (switch-case dạng Python)
            if msg_type == "READY":  # ready
                send_msg = f"[{user}] is ready: {message}"
            elif msg_type == "CHAT":  # chat
                send_msg = f"[{user}] says: {message}"
            else:
                send_msg = f"[{user}] sent unknown type ({msg_type}): {message}"

            # Broadcast cho tất cả client đang kết nối (chỉ gửi message này 1 lần)
            closed_clients = set()
            for client in connected_clients:
                try:
                    await client.send_text(f"Broadcast: {send_msg}")
                    print("Sent message: '", send_msg ,"' to client:", client)
                except Exception as e:
                    print("Send error:", e)
                    closed_clients.add(client)

            # Loại các client đã disconnect khỏi danh sách
            connected_clients.difference_update(closed_clients)
            print(f"Server broadcasted: {send_msg}")

    except WebSocketDisconnect:
        print("Client disconnected")
        connected_clients.remove(websocket)
        print(f"Client removed. Connected_clients: {(connected_clients)}")

    except Exception as e:
        print("Other error:", e)
        if websocket in connected_clients:
            connected_clients.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
