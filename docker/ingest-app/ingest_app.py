import asyncio
import websockets
import json
import logging
from aiokafka import AIOKafkaProducer

# ✅ Structured Logging Setup
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = logging.FileHandler("/mnt/spark/logs/bitcoin_transactions.log")
log_handler.setFormatter(log_formatter)
LOGGER = logging.getLogger("BitcoinWebSocketApp")
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(log_handler)

# ✅ WebSocket URL for Blockchain API
WEBSOCKET_URL = "wss://ws.blockchain.info/inv"

# ✅ Kafka Configuration
KAFKA_TOPIC_TRANSACTIONS = "unconfirmed_transactions"
KAFKA_TOPIC_LOGS = "spark-logs"
KAFKA_BROKER = "kafka-broker:9092"

# ✅ Initialize Async Kafka Producer
producer = None  # Will be initialized in the main function


async def setup_kafka():
    """
    Initializes the Kafka producer and waits until it is ready.
    """
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    await producer.start()
    LOGGER.info("Kafka producer started successfully.")


async def subscribe_to_unconfirmed_transactions():
    """
    Connects to the WebSocket and listens for unconfirmed Bitcoin transactions.
    """
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        # ✅ Subscribe to unconfirmed transactions
        await websocket.send(json.dumps({"op": "unconfirmed_sub"}))
        LOGGER.info("Subscribed to unconfirmed transactions.")

        # ✅ Listen for messages indefinitely
        while True:
            try:
                message = await websocket.recv()
                await process_message(message)
            except websockets.exceptions.ConnectionClosed as e:
                LOGGER.error(f"WebSocket connection closed: {e}")
                break
            except Exception as e:
                LOGGER.error(f"Unexpected error: {e}", exc_info=True)


async def process_message(message):
    """
    Parses WebSocket messages and sends transaction data to Kafka.
    """
    try:
        data = json.loads(message)
        if data.get("op") == "utx":
            transaction = data.get("x", {})

            # ✅ Log transaction
            log_transaction(transaction)

            # ✅ Send transaction data to Kafka
            await producer.send(KAFKA_TOPIC_TRANSACTIONS, transaction)
            LOGGER.info(f"Transaction sent to Kafka: {transaction.get('hash', 'N/A')}")

    except json.JSONDecodeError:
        LOGGER.error("Error decoding JSON message", exc_info=True)


def log_transaction(transaction):
    """
    Logs transaction details in a structured format.
    """
    tx_hash = transaction.get("hash", "N/A")
    tx_index = transaction.get("tx_index", "N/A")
    timestamp = transaction.get("time", "N/A")
    inputs = transaction.get("inputs", [])
    outputs = transaction.get("out", [])

    log_entry = {
        "@timestamp": timestamp,
        "log": f"📦 Transaction: {json.dumps(transaction, indent=2)}"
    }

    LOGGER.info(json.dumps(log_entry))

    # ✅ Send structured logs to Kafka log topic
    asyncio.create_task(producer.send(KAFKA_TOPIC_LOGS, log_entry))


async def main():
    """
    Main function that sets up Kafka and starts the WebSocket listener.
    """
    await setup_kafka()
    try:
        await subscribe_to_unconfirmed_transactions()
    finally:
        await producer.stop()
        LOGGER.info("Kafka producer stopped.")


# ✅ Run the asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
