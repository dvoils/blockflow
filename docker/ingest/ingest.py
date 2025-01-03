import asyncio
import websockets
import json
import logging
from confluent_kafka import Producer

# Setup logging
logging.basicConfig(filename="bitcoin_transactions.log", level=logging.INFO, format='%(asctime)s - %(message)s')

# WebSocket URL for Blockchain API
WEBSOCKET_URL = "wss://ws.blockchain.info/inv"

# Kafka configuration
kafka_conf = {
    'bootstrap.servers': "kafka-service.kafka.svc.cluster.local:9092"
}

# Create a Kafka producer
producer = Producer(**kafka_conf)

def acked(err, msg):
    if err is not None:
        logging.error(f"Failed to deliver message: {err}")
    else:
        logging.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

async def subscribe_to_unconfirmed_transactions():
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        # Subscribe to unconfirmed transactions
        await websocket.send(json.dumps({"op": "unconfirmed_sub"}))
        print("Subscribed to unconfirmed transactions")
        logging.info("Subscribed to unconfirmed transactions")

        # Listen for messages indefinitely
        while True:
            message = await websocket.recv()
            process_message(message)

def process_message(message):
    logging.info(f"Raw message: {message}")
    try:
        data = json.loads(message)
        if data["op"] == "utx":
            transaction = data["x"]
            log_transaction(transaction)
    except json.JSONDecodeError:
        print("Error decoding JSON message")
        logging.error("Error decoding JSON message")

def log_transaction(transaction):
    # Serialize transaction data as JSON to send to Kafka
    tx_data = json.dumps({
        'hash': transaction.get("hash", "N/A"),
        'tx_index': transaction.get("tx_index", "N/A"),
        'time': transaction.get("time", "N/A"),
        'inputs': [{ 
            'input_address': inp["prev_out"].get("addr", "N/A"), 
            'input_value': inp["prev_out"].get("value", "N/A")
        } for inp in transaction.get("inputs", [])],
        'outputs': [{
            'output_address': out.get("addr", "N/A"),
            'output_value': out.get("value", "N/A")
        } for out in transaction.get("out", [])]
    })
    producer.produce('unconfirmed_transactions', value=tx_data, callback=acked)
    producer.flush()

    print(f"Transaction logged and sent to Kafka: {transaction.get('hash', 'N/A')}")

async def main():
    await subscribe_to_unconfirmed_transactions()

# Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
