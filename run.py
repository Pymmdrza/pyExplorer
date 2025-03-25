from app import app
from websocket_manager import WebSocketManager
import asyncio
import threading
from app.routes import handle_new_transaction  # Fixed import

def run_websocket():
    async def start_websocket():
        ws_manager = WebSocketManager()
        ws_manager.add_transaction_callback(handle_new_transaction)
        while True:
            connected = await ws_manager.connect()
            if connected:
                await ws_manager.listen()
            await asyncio.sleep(5)  # Wait before reconnecting

    asyncio.run(start_websocket())

if __name__ == '__main__':
    # Start WebSocket connection in a separate thread
    websocket_thread = threading.Thread(target=run_websocket, daemon=True)
    websocket_thread.start()

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)