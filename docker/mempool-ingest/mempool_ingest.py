import asyncio
import json
import logging
import signal
import random

import websockets
from aiokafka import AIOKafkaProducer
from jsonschema import validate, ValidationError

# Configuration
KAFKA_BOOTSTRAP_SERVERS = "kafka-broker:9092"
TOPIC = "mempool_blocks"
WS_URL = "wss://mempool.space/api/v1/ws"

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# JSON Schema for mempool-blocks
mempool_blocks_schema = {
    "type": "object",
    "properties": {
        "mempool-blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "blockSize": {"type": "number"},
                    "blockVSize": {"type": "number"},
                    "nTx": {"type": "integer"},
                    "totalFees": {"type": "number"},
                    "medianFee": {"type": "number"},
                    "feeRange": {
                        "type": "array",
                        "items": {"type": "number"}
                    }
                },
                "required": ["blockSize", "blockVSize", "nTx", "totalFees", "medianFee", "feeRange"]
            }
        }
    },
    "required": ["mempool-blocks"]
}

def validate_mempool_message(data):
    try:
        validate(instance=data, schema=mempool_blocks_schema)
        return True
    except ValidationError as e:
        logging.error("Schema validation failed: %s", e)
        return False

shutdown_event = asyncio.Event()

def handle_shutdown():
    logging.info("Shutdown signal received. Exiting...")
    shutdown_event.set()

async def produce_to_kafka(producer, message):
    try:
        await producer.send_and_wait(TOPIC, message.encode("utf-8"))
        logging.info("Produced message to Kafka")
    except Exception as e:
        logging.error("Failed to send message to Kafka: %s", e)

async def stream_mempool_blocks():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        backoff = 1
        while not shutdown_event.is_set():
            try:
                async with websockets.connect(
                    WS_URL,
                    ping_interval=20,
                    ping_timeout=10
                ) as ws:
                    await ws.send(json.dumps({"action": "want", "data": ["mempool-blocks"]}))
                    logging.info("Subscribed to mempool-blocks")

                    while not shutdown_event.is_set():
                        raw_message = await asyncio.wait_for(ws.recv(), timeout=30)
                        try:
                            message = json.loads(raw_message)
                        except json.JSONDecodeError:
                            logging.warning("Received non-JSON message: %s", raw_message)
                            continue

                        if not validate_mempool_message(message):
                            continue

                        await produce_to_kafka(producer, raw_message)

                    backoff = 1
            except (websockets.ConnectionClosedError, asyncio.TimeoutError) as e:
                logging.warning("Connection lost: %s", e)
                sleep_time = backoff + random.uniform(0, backoff)
                logging.info("Reconnecting in %.2f seconds...", sleep_time)
                await asyncio.sleep(sleep_time)
                backoff = min(backoff * 2, 60)
            except Exception as e:
                logging.error("Unexpected error: %s", e)
                await asyncio.sleep(5)
    finally:
        await producer.stop()
        logging.info("Kafka producer closed.")

async def main():
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handle_shutdown)
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown)
    await stream_mempool_blocks()

if __name__ == "__main__":
    asyncio.run(main())
