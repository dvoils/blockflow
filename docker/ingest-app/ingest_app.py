import asyncio
import json
import websockets
from aiokafka import AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = "kafka-broker:9092"  # Replace with your broker address
TOPIC = "unconfirmed_transactions"
WS_URL = "wss://ws.blockchain.info/inv"

async def produce_to_kafka(producer, message):
    """
    Sends the message to Kafka asynchronously.
    """
    try:
        await producer.send_and_wait(TOPIC, message.encode("utf-8"))
        print("Produced transaction to Kafka:", message)
    except Exception as e:
        print("Failed to deliver message to Kafka:", e)

async def stream_data():
    """
    Connects to the Blockchain.com WebSocket, subscribes to the unconfirmed
    transactions stream, and forwards each message to Kafka.
    """
    # Initialize and start the asynchronous Kafka producer
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        async with websockets.connect(WS_URL) as ws:
            # Send the subscription message according to the API documentation
            sub_msg = json.dumps({"op": "unconfirmed_sub"})
            await ws.send(sub_msg)
            print("WebSocket connection opened and subscription sent.")
            while True:
                message = await ws.recv()
                try:
                    # Optionally process JSON data
                    data = json.loads(message)
                except json.JSONDecodeError:
                    print("Received non-JSON message:", message)
                    continue

                # Produce the message to Kafka asynchronously
                await produce_to_kafka(producer, message)
    except Exception as e:
        print("Error with WebSocket connection:", e)
    finally:
        # Ensure the producer is properly stopped
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(stream_data())
