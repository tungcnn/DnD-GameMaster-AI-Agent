import os
import websockets
import asyncio

class WebSocketService:
    async def send_message(self, message: str):
        WS_ENDPOINT = os.getenv("WS_ENDPOINT", "ws://localhost:8000/ws")
        WS_RECONNECT_INTERVAL = int(os.getenv("WS_RECONNECT_INTERVAL", 5))

        try:
            async with websockets.connect(WS_ENDPOINT) as ws:
                print(f"Connected to {WS_ENDPOINT}")
                # Gửi message đúng 1 lần
                await ws.send(message)
                print(f"Client sent: {message}")
        except Exception as e:
            print(f"Connection lost: {e}. Reconnecting in {WS_RECONNECT_INTERVAL} seconds...")
            await asyncio.sleep(WS_RECONNECT_INTERVAL)

ws_service = WebSocketService()
