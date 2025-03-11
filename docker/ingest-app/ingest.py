import asyncio
import json
import websockets

WS_URL = "wss://ws.blockchain.info/inv"

async def stream_payload():
    async with websockets.connect(WS_URL) as ws:
        # Subscribe to unconfirmed transactions
        subscription = json.dumps({"op": "unconfirmed_sub"})
        await ws.send(subscription)
        print("Subscribed to unconfirmed transactions. Listening for data...\n")
        
        while True:
            message = await ws.recv()
            try:
                data = json.loads(message)
                print("Received transaction payload:")
                print(json.dumps(data, indent=2))
                print("-" * 80)  # Separator for readability
            except json.JSONDecodeError:
                print("Received non-JSON payload:", message)

if __name__ == '__main__':
    try:
        asyncio.run(stream_payload())
    except KeyboardInterrupt:
        print("Stopped by user.")
