import asyncio
import websockets
import json
import logging

# Setup logging to a file for better tracking
logging.basicConfig(filename="bitcoin_transactions.log", level=logging.INFO, format='%(asctime)s - %(message)s')

# WebSocket URL for Blockchain API
WEBSOCKET_URL = "wss://ws.blockchain.info/inv"

async def subscribe_to_unconfirmed_transactions():
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        # Subscribe to unconfirmed transactions
        await websocket.send(json.dumps({
            "op": "unconfirmed_sub"
        }))
        print("Subscribed to unconfirmed transactions")
        logging.info("Subscribed to unconfirmed transactions")

        # Listen for messages indefinitely
        while True:
            message = await websocket.recv()
            process_message(message)

def process_message(message):
    # Parse the incoming message as JSON
    (f"Raw message: {message}")
    try:
        data = json.loads(message)
        if data["op"] == "utx":
            transaction = data["x"]
            log_transaction(transaction)
    except json.JSONDecodeError:
        print("Error decoding JSON message")
        logging.error("Error decoding JSON message")

def log_transaction(transaction):
    # Extract necessary details from the transaction
    tx_hash = transaction.get("hash", "N/A")
    tx_index = transaction.get("tx_index", "N/A")
    time = transaction.get("time", "N/A")
    inputs = transaction.get("inputs", [])
    outputs = transaction.get("out", [])
    
    # Log transaction details
    logging.info(f"Transaction Hash: {tx_hash}, Time: {time}")
    logging.info(f"Transaction Index: {tx_index}")
    
    # Log input addresses and values
    for inp in inputs:
        input_address = inp["prev_out"].get("addr", "N/A")
        input_value = inp["prev_out"].get("value", "N/A")
        logging.info(f"Input Address: {input_address}, Input Value: {input_value}")

    # Log output addresses and values
    for out in outputs:
        output_address = out.get("addr", "N/A")
        output_value = out.get("value", "N/A")
        logging.info(f"Output Address: {output_address}, Output Value: {output_value}")
    
    print(f"Transaction logged: {tx_hash}")

async def main():
    await subscribe_to_unconfirmed_transactions()

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
