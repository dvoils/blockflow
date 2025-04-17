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
TOPIC = "confirmed_blocks"
WS_URL = "wss://mempool.space/api/v1/ws"

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# JSON Schema for confirmed block
confirmed_block_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "height": {"type": "integer"},
        "timestamp": {"type": "integer"},
        "tx_count": {"type": "integer"}
    },
    "required": ["id", "height", "timestamp", "tx_count"]
}

def validate_block_message(data):
    try:
        validate(instance=data, schema=confirmed_block_schema)
        return True
    except ValidationError as e:
        logging.error("❌ Schema validation failed: %s", e)
        return False

shutdown_event = asyncio.Event()

def handle_shutdown():
    logging.info("🛑 Shutdown signal received.")
    shutdown_event.set()

async def produce_to_kafka(producer, message):
    try:
        await producer.send_and_wait(TOPIC, json.dumps(message).encode("utf-8"))
        logging.info("✅ Produced confirmed block: height %s", message.get("height"))
    except Exception as e:
        logging.error("❌ Kafka send failed: %s", e)

async def stream_confirmed_blocks():
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        backoff = 1
        while not shutdown_event.is_set():
            try:
                async with websockets.connect(
                    WS_URL,
                    ping_interval=None,
                    ping_timeout=None,
                    max_queue=None
                ) as ws:
                    # Start a background ping task
                    async def ping_forever():
                        while not shutdown_event.is_set():
                            try:
                                await ws.ping()
                                logging.debug("📡 Sent ping")
                                await asyncio.sleep(15)
                            except Exception as e:
                                logging.warning("💥 Ping error: %s", e)
                                break

                    asyncio.create_task(ping_forever())

                    # Subscribe to confirmed blocks
                    await ws.send(json.dumps({"action": "want", "data": ["blocks"]}))
                    logging.info("🔗 Subscribed to confirmed blocks")

                    # Main receive loop
                    while not shutdown_event.is_set():
                        try:
                            logging.debug("⏳ Waiting for block...")
                            raw_message = await asyncio.wait_for(ws.recv(), timeout=300)
                            message = json.loads(raw_message)
                            block = message.get("block")
                            if block and validate_block_message(block):
                                await produce_to_kafka(producer, block)
                            else:
                                logging.warning("⚠️ Skipped invalid or empty block message.")
                        except asyncio.TimeoutError:
                            logging.info("⌛ No block yet. Still connected...")
                        except (json.JSONDecodeError, KeyError) as e:
                            logging.warning("⚠️ Invalid message format: %s", e)
                        except Exception as e:
                            logging.error("🔥 Unexpected error while receiving: %s", e)
                            break

                    backoff = 1  # reset backoff after a good connection
            except (websockets.ConnectionClosedError, asyncio.TimeoutError) as e:
                logging.warning("🔌 Disconnected: %s", e)
                sleep_time = backoff + random.uniform(0, backoff)
                logging.info("🔁 Reconnecting in %.2f seconds...", sleep_time)
                await asyncio.sleep(sleep_time)
                backoff = min(backoff * 2, 60)
            except Exception as e:
                logging.error("🔥 Unexpected connection error: %s", e)
                await asyncio.sleep(5)
    finally:
        await producer.stop()
        logging.info("👋 Kafka producer stopped.")

async def main():
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handle_shutdown)
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown)
    await stream_confirmed_blocks()

if __name__ == "__main__":
    asyncio.run(main())
