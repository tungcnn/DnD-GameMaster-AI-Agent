import os
import websockets
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect

class WebSocketService:
    def __init__(self):
        self.connected_clients = []

    def remove_websocket_list_dic(self, data_list):
        filtered_data = []
        for d in data_list:
            filtered = self.remove_websocket_dic(d)
            filtered_data.append(filtered)
        return filtered_data

    def remove_websocket_dic(self, data):
        filtered_data = {k: v for k, v in data.items() if k != 'websocket'}
        return filtered_data

    async def handle_connect(self, websocket: WebSocket):
        await websocket.accept()
        websocket_id = hex(id(websocket))
        client_obj = {
            "id": websocket_id,
            "user": websocket_id,
            "type": "",
            "message": "",
            "websocket": websocket
        }
        self.connected_clients.append(client_obj)
        return client_obj

    async def handle_receive(self, websocket, client_obj, openai_service):
        websocket_id = hex(id(websocket))
        try:
            while True:
                data_text = await websocket.receive_text()
                print(f"Server received: {data_text}")

                # Parse JSON message
                try:
                    data = json.loads(data_text)
                except Exception as e:
                    error_msg = f"JSON parse error: {str(e)}. Message must be like: {{\"user\": str, \"type\": str, \"message\": str}} (type: JOIN/CHAT)"
                    try:
                        await websocket.send_text(error_msg)
                    except Exception as err:
                        print("Send error to client:", err)
                    continue

                json_user = data.get("user", websocket_id)
                json_type = data.get("type", "Unknown")
                json_message = data.get("message", "")

                if json_type == "PING":
                    print(f"PING SERVER")
                else:    
                    closed_clients = []
                    # Broadcast logic
                    for client in self.connected_clients:
                        if client["id"] == websocket_id:
                            client["user"] = json_user
                            client["type"] = json_type
                            if json_type == "JOIN":
                                client["message"] = ""
                                status = {
                                    "id": "STATUS",
                                    "user": "STATUS",
                                    "type": "STATUS",
                                    "message": json.dumps(self.remove_websocket_list_dic(self.connected_clients))
                                }
                                for joiner in self.connected_clients:
                                    try:
                                        await joiner["websocket"].send_text(f"{json.dumps(self.remove_websocket_dic(status))}")
                                    except Exception as e:
                                        print("Send error:", e)
                            elif json_type == "CHAT":
                                client["message"] = json_message
                            else:
                                client["message"] = f"Unknown type: {json_type}"

                    all_have_message = all(client["message"] != "" for client in self.connected_clients)

                    if all_have_message:
                        for client in self.connected_clients:
                            try:
                                await client["websocket"].send_text(f"{json.dumps(self.remove_websocket_dic(client_obj))}")
                                print("Sent message: '", client_obj, "' to client:", websocket_id)
                                start_thinking = {
                                    "id": "GAME_MASTER",
                                    "user": "GAME_MASTER",
                                    "type": "THINKING",
                                    "message": "START"
                                }
                                await client["websocket"].send_text(f"{json.dumps(self.remove_websocket_dic(start_thinking))}")
                            except Exception as e:
                                print("Send error:", e)
                                closed_clients.append(websocket_id)

                        # call OpenAPI here
                        user_messages = [(client["user"], client["message"]) for client in self.connected_clients]
                        reply = await openai_service.chat(user_messages, "user-123")
                        # end call OpenAPI here

                        for client in self.connected_clients:
                            try:
                                end_thinking = {
                                    "id": "GAME_MASTER",
                                    "user": "GAME_MASTER",
                                    "type": "THINKING",
                                    "message": "END"
                                }
                                await client["websocket"].send_text(f"{json.dumps(self.remove_websocket_dic(end_thinking))}")

                                game_master_respone = {
                                    "id": "GAME_MASTER",
                                    "user": "GAME_MASTER",
                                    "type": "CHAT",
                                    "message": reply
                                }
                                await client["websocket"].send_text(f"{json.dumps(self.remove_websocket_dic(game_master_respone))}")
                                client["message"] = ""
                                print("Sent message: '", game_master_respone, "' to client:", websocket_id)
                            except Exception as e:
                                print("Send error:", e)
                                closed_clients.append(websocket_id)
                    else:
                        for client in self.connected_clients:
                            try:
                                await client["websocket"].send_text(f"{json.dumps(self.remove_websocket_dic(client_obj))}")
                                print("Sent message: '", client_obj, "' to client:", websocket_id)
                            except Exception as e:
                                print("Send error:", e)
                                closed_clients.append(websocket_id)

                    # Remove disconnected clients
                    for close in closed_clients:
                        for client in self.connected_clients:
                            if client["id"] == close:
                                self.connected_clients.remove(client)
        except WebSocketDisconnect:
            await self.handle_disconnect(websocket, websocket_id)
        except Exception as e:
            print("Other error:", e)
            for client in self.connected_clients[:]:
                if client["websocket"] == websocket:
                    self.connected_clients.remove(client)
                print(f"Client removed. Connected_clients: {(self.connected_clients)}")

    async def handle_disconnect(self, websocket, websocket_id):
        print(f"Client disconnected: {websocket_id}")
        disconnected_clients = next(
            (client for client in self.connected_clients if client["id"] == websocket_id),
            None
        )
        if disconnected_clients:
            disconnected_clients["type"] = "LEFT"
        for client in self.connected_clients[:]:
            if client["websocket"] == websocket:
                self.connected_clients.remove(client)
            else:
                await client["websocket"].send_text(f"{json.dumps(self.remove_websocket_dic(disconnected_clients))}")
            print(f"Client removed. Connected_clients: {(self.connected_clients)}")

        status = {
            "id": "STATUS",
            "user": "STATUS",
            "type": "STATUS",
            "message": json.dumps(self.remove_websocket_list_dic(self.connected_clients))
        }
        for joiner in self.connected_clients:
            try:
                await joiner["websocket"].send_text(f"{json.dumps(self.remove_websocket_dic(status))}")
            except Exception as e:
                print("Send error:", e)

    async def client_send_message(self, message: str):
        WS_ENDPOINT = os.getenv("WS_ENDPOINT", "ws://localhost:8000/ws")
        WS_RECONNECT_INTERVAL = int(os.getenv("WS_RECONNECT_INTERVAL", 5))

        try:
            async with websockets.connect(WS_ENDPOINT) as ws:
                print(f"Connected to {WS_ENDPOINT}")
                await ws.send(message)
                print(f"Client sent: {message}")
        except Exception as e:
            print(f"Connection lost: {e}. Reconnecting in {WS_RECONNECT_INTERVAL} seconds...")
            await asyncio.sleep(WS_RECONNECT_INTERVAL)

ws_service = WebSocketService()
