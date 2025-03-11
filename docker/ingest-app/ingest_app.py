import asyncio
import json
import logging
import websockets
from aiokafka import AIOKafkaProducer
from jsonschema import validate, ValidationError

# Configuration
KAFKA_BOOTSTRAP_SERVERS = "kafka-broker:9092"  # Replace with your broker address
TOPIC = "unconfirmed_transactions"
WS_URL = "wss://ws.blockchain.info/inv"

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Define the JSON schema for unconfirmed transactions
transaction_schema = {
    "type": "object",
    "properties": {
        "op": {"type": "string", "enum": ["utx"]},
        "x": {
            "type": "object",
            "properties": {
                "lock_time": {"type": "integer"},
                "ver": {"type": "integer"},
                "size": {"type": "integer"},
                "inputs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sequence": {"type": "integer"},
                            "prev_out": {
                                "type": "object",
                                "properties": {
                                    "spent": {"type": "boolean"},
                                    "tx_index": {"type": "integer"},
                                    "type": {"type": "integer"},
                                    "addr": {"type": "string"},
                                    "value": {"type": "number"},
                                    "n": {"type": "integer"},
                                    "script": {"type": "string"}
                                },
                                "required": ["spent", "tx_index", "type", "addr", "value", "n", "script"]
                            },
                            "script": {"type": "string"}
                        },
                        "required": ["sequence", "prev_out", "script"]
                    }
                },
                "time": {"type": "integer"},
                "tx_index": {"type": "integer"},
                "vin_sz": {"type": "integer"},
                "hash": {"type": "string"},
                "vout_sz": {"type": "integer"},
                "relayed_by": {"type": "string"},
                "out": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "spent": {"type": "boolean"},
                            "tx_index": {"type": "integer"},
                            "type": {"type": "integer"},
                            "addr": {"type": "string"},
                            "value": {"type": "number"},
                            "n": {"type": "integer"},
                            "script": {"type": "string"}
                        },
                        "required": ["spent", "tx_index", "type", "addr", "value", "n", "script"]
                    }
                }
            },
            "required": ["lock_time", "ver", "size", "inputs", "time", "tx_index", "vin_sz", "hash", "vout_sz", "relayed_by", "out"]
        }
    },
    "required": ["op", "x"]
}

def validate_transaction(message_data):
    """
    Validate the transaction JSON against the schema.
    Returns True if valid, False otherwise.
    """
    try:
        validate(instance=message_data, schema=transaction_schema)
        return True
    except ValidationError as e:
        logging.error("Schema validation error: %s", e)
        return False

async def produce_to_kafka(producer, message):
    """
    Sends the message to Kafka asynchronously.
    """
    try:
        await producer.send_and_wait(TOPIC, message.encode("utf-8"))
        logging.info("Produced transaction to Kafka: %s", message)
    except Exception as e:
        logging.error("Failed to deliver message to Kafka: %s", e)

async def stream_data():
    """
    Connects to the Blockchain.com WebSocket, subscribes to the unconfirmed
    transactions stream, validates each message against the schema,
    and forwards valid messages to Kafka.
    """
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        async with websockets.connect(WS_URL) as ws:
            # Subscribe to unconfirmed transactions
            sub_msg = json.dumps({"op": "unconfirmed_sub"})
            await ws.send(sub_msg)
            logging.info("WebSocket connection opened and subscription sent.")

            while True:
                message = await ws.recv()
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    logging.error("Received non-JSON message: %s", message)
                    continue

                # Validate the JSON message against the schema
                if not validate_transaction(data):
                    logging.warning("Invalid transaction schema, skipping message.")
                    continue

                # Produce valid messages to Kafka
                await produce_to_kafka(producer, message)

    except Exception as e:
        logging.error("Error with WebSocket connection: %s", e)
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(stream_data())
