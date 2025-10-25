import os
import websockets
import asyncio

class WebSocketService:
    async def send_message(self, message: str):
        uri = os.getenv("WS_ENDPOINT")  # using key WS_ENDPOINT in .env
        async with websockets.connect(uri) as websocket:
            await websocket.send(message)
            print(f"Client sent: {message}")
            response = await websocket.recv()
            print("Client received:", response)
            await asyncio.sleep(3)  # keep connect for test

ws_service = WebSocketService()
