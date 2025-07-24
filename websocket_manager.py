import asyncio
import websockets
import json
import logging

class WebSocketManager:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.callbacks = []
        logging.basicConfig(level=logging.INFO)

    async def connect(self):
        try:
            logging.info("Attempting to connect to blockchain websocket...")
            self.ws = await websockets.connect('wss://ws.blockchain.info/inv')
            self.connected = True
            await self.subscribe_to_transactions()
            logging.info("Successfully connected and subscribed to transactions")
            return True
        except Exception as e:
            logging.error(f"WebSocket connection error: {str(e)}")
            return False

    async def subscribe_to_transactions(self):
        try:
            subscribe_message = json.dumps({
                "op": "unconfirmed_sub"
            })
            await self.ws.send(subscribe_message)
            logging.info("Subscribed to unconfirmed transactions")
        except Exception as e:
            logging.error(f"Error subscribing to transactions: {str(e)}")
            raise

    def add_transaction_callback(self, callback):
        self.callbacks.append(callback)
        logging.info("Added new transaction callback")

    async def listen(self):
        while self.connected:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                if data.get('op') == 'utx':
                    tx = data.get('x', {})
                    formatted_tx = {
                        'hash': tx.get('hash'),
                        'time': tx.get('time'),
                        'amount': sum(out.get('value', 0) for out in tx.get('out', [])) / 1e8,
                        'from': [inp.get('prev_out', {}).get('addr') for inp in tx.get('inputs', [])],
                        'to': [out.get('addr') for out in tx.get('out', [])]
                    }
                    for callback in self.callbacks:
                        callback(formatted_tx)
            except websockets.exceptions.ConnectionClosed:
                logging.error("WebSocket connection closed unexpectedly")
                self.connected = False
                break
            except Exception as e:
                logging.error(f"WebSocket error while listening: {str(e)}")
                self.connected = False
                break

    async def close(self):
        if self.ws:
            try:
                await self.ws.close()
                self.connected = False
                logging.info("WebSocket connection closed")
            except Exception as e:
                logging.error(f"Error closing WebSocket: {str(e)}")
