import asyncio
import json
import logging
import signal
import sys
import random

import websockets
from aiokafka import AIOKafkaProducer
from jsonschema import validate, ValidationError

# Configuration
KAFKA_BOOTSTRAP_SERVERS = "kafka-broker:9092"
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
    try:
        validate(instance=message_data, schema=transaction_schema)
        return True
    except ValidationError as e:
        logging.error("Schema validation error: %s", e)
        return False

async def produce_to_kafka(producer, message):
    try:
        await producer.send_and_wait(TOPIC, message.encode("utf-8"))
        logging.info("Produced transaction to Kafka")
    except Exception as e:
        logging.error("Failed to deliver message to Kafka: %s", e)

shutdown_event = asyncio.Event()

def handle_shutdown():
    logging.info("Received termination signal. Shutting down gracefully...")
    shutdown_event.set()

async def stream_data():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        backoff = 1  # Initial backoff in seconds
        while not shutdown_event.is_set():
            try:
                async with websockets.connect(
                    WS_URL,
                    ping_interval=20,
                    ping_timeout=10
                ) as ws:
                    sub_msg = json.dumps({"op": "unconfirmed_sub"})
                    await ws.send(sub_msg)
                    logging.info("WebSocket connection opened and subscription sent.")
                    backoff = 1  # reset backoff after successful connect

                    while not shutdown_event.is_set():
                        message = await asyncio.wait_for(ws.recv(), timeout=30)
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            logging.error("Received non-JSON message: %s", message)
                            continue

                        if not validate_transaction(data):
                            logging.warning("Invalid transaction schema, skipping message.")
                            continue

                        await produce_to_kafka(producer, message)

            except (websockets.ConnectionClosedError, asyncio.TimeoutError) as e:
                logging.warning("WebSocket connection closed or timed out: %s", e)
                sleep_time = backoff + random.uniform(0, backoff * 0.5)
                logging.info("Reconnecting in %.2f seconds", sleep_time)
                await asyncio.sleep(sleep_time)
                backoff = min(backoff * 2, 60)  # cap at 60 seconds

            except Exception as e:
                logging.error("Unhandled exception: %s", e)
                sleep_time = backoff + random.uniform(0, backoff * 0.5)
                await asyncio.sleep(sleep_time)
                backoff = min(backoff * 2, 60)

    finally:
        await producer.stop()
        logging.info("Kafka producer closed. Exiting stream_data().")

async def main():
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown)
    loop.add_signal_handler(signal.SIGINT, handle_shutdown)

    await stream_data()

if __name__ == "__main__":
    asyncio.run(main())
