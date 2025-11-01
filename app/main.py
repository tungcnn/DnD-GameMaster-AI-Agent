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

connected_clients = []
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_id = hex(id(websocket))

    # Khi client connect, tạo object client và add vào list
    client_obj = {
        "id": websocket_id,
        "user": websocket_id,         # sẽ cập nhật khi nhận message đầu tiên
        "type": "",
        "message": "",
        "websocket": websocket     # lưu luôn object websocket để gửi message
    }
    connected_clients.append(client_obj)
    print(f"Client connected: {websocket_id}. Total: {len(connected_clients)}")

    # Khi client kết nối, gửi danh sách các client đang connected cho FE
    for client in connected_clients:
        try:
            await client["websocket"].send_text(f"{json.dumps(remove_websocket_list_dic(connected_clients))}")
        except Exception as e:
            print("Send error:", e)

    try:
        while True:
            # Chỉ gửi đúng 1 lần mỗi khi nhận được message
            data_text = await websocket.receive_text()
            print(f"Server received: {data_text}")

            # Convert JSON dạng {"user": "string", "type": "JOIN"/"CHAT", "message": "string"}
            try:
                data = json.loads(data_text)
            except Exception as e:
                # Gửi thông báo lỗi về cho client vừa gửi
                error_msg = f"JSON parse error: {str(e)}. Message must be like: {{\"user\": str, \"type\": str, \"message\": str}} (type: JOIN/CHAT)"
                try:
                    await websocket.send_text(error_msg)
                except Exception as err:
                    print("Send error to client:", err)
                continue  # bỏ qua broadcast

            json_user = data.get("user", websocket_id)
            json_type = data.get("type", "Unknown")
            json_message = data.get("message", "")

            # Broadcast cho tất cả client đang kết nối (chỉ gửi message này 1 lần)
            closed_clients = []
            for client in connected_clients:
                if client["id"] == websocket_id:
                    client["user"] = json_user
                    client["type"] = json_type
                    if json_type == "JOIN":
                        client["message"] = ""
                    elif json_type == "CHAT":
                        client["message"] = json_message
                    else:
                        client["message"] = f"Unknown type: {json_type}"

            all_have_message = all(client["message"] != "" for client in connected_clients)
            
            if all_have_message:
                for client in connected_clients:
                    try:
                        await client["websocket"].send_text(f"{json.dumps(remove_websocket_dic(client_obj))}")
                        print("Sent message: '", client_obj ,"' to client:", websocket_id)
                    except Exception as e:
                        print("Send error:", e)
                        closed_clients.append(websocket_id)          

                # call OpenAPI here
                user_messages = [(client["user"], client["message"]) for client in connected_clients]
                reply = await openai_service.chat(user_messages, "user-123")
                # end call OpenAPI here

                for client in connected_clients:
                    try:
                        
                        game_master_respone = {
                            "id": "GAME_MASTER",
                            "user": "GAME_MASTER", 
                            "type": "CHAT",
                            "message": reply  # respone OPEN API
                        }

                        await client["websocket"].send_text(f"{json.dumps(remove_websocket_dic(game_master_respone))}")
                        client["message"] = ""
                        print("Sent message: '", game_master_respone ,"' to client:", websocket_id)
                    except Exception as e:
                        print("Send error:", e)
                        closed_clients.append(websocket_id)
            else:
                for client in connected_clients:
                    try:
                        await client["websocket"].send_text(f"{json.dumps(remove_websocket_dic(client_obj))}")
                        print("Sent message: '", client_obj ,"' to client:", websocket_id)
                    except Exception as e:
                        print("Send error:", e)
                        closed_clients.append(websocket_id)            

            # Loại các client đã disconnect khỏi danh sách
            for close in closed_clients:  # closed_clients là list các object cần xóa
                for client in connected_clients:
                    if client["id"] == close["id"]:
                        connected_clients.remove(client)
            print(f"Server broadcasted: {json_message}")

    except WebSocketDisconnect:
        print(f"Client disconnected: {websocket_id}")
        disconnected_clients = next(
            (client for client in connected_clients if client["id"] == websocket_id),
            None
        )
        
        for client in connected_clients[:]:  # Duyệt qua bản copy để xóa an toàn
            if client["websocket"] == websocket:
                connected_clients.remove(client)
            else:
                await client["websocket"].send_text(f"Disconnected: {json.dumps(remove_websocket_dic(disconnected_clients))}")
            print(f"Client removed. Connected_clients: {(connected_clients)}")

    except Exception as e:
        print("Other error:", e)
        for client in connected_clients[:]:  # Duyệt qua bản copy để xóa an toàn
            if client["websocket"] == websocket:
                connected_clients.remove(client)
            print(f"Client removed. Connected_clients: {(connected_clients)}")

def remove_websocket_list_dic(data_list):
    filtered_data = []
    for d in data_list:
        filtered = remove_websocket_dic(d)
        filtered_data.append(filtered)
    return filtered_data

def remove_websocket_dic(data):
    filtered_data = {k: v for k, v in data.items() if k != 'websocket'}
    return filtered_data
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
