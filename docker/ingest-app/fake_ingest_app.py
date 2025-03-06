import json
import time
import random
from confluent_kafka import Producer

# Kafka configuration
kafka_conf = {
    'bootstrap.servers': "kafka-broker:9092"  # Replace with your broker address
}

# Create a Kafka producer
producer = Producer(**kafka_conf)

def acked(err, msg):
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def generate_fake_transaction():
    """Generate a fake Bitcoin transaction."""
    transaction = {
        "hash": f"tx-{random.randint(1000, 9999)}",
        "tx_index": random.randint(1000, 9999),
        "time": int(time.time()),
        "inputs": [
            {
                "input_address": f"addr-{random.randint(1, 1000)}",
                "input_value": random.randint(1, 10000)
            }
        ],
        "outputs": [
            {
                "output_address": f"addr-{random.randint(1, 1000)}",
                "output_value": random.randint(1, 10000)
            }
        ]
    }
    return transaction

def produce_fake_data(topic, interval=1):
    """Produce fake transactions to the specified Kafka topic."""
    try:
        while True:
            transaction = generate_fake_transaction()
            transaction_json = json.dumps(transaction)
            producer.produce(topic, value=transaction_json, callback=acked)
            producer.poll(0)  # Trigger delivery reports
            print(f"Produced transaction: {transaction}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopping producer...")
    finally:
        producer.flush()  # Ensure all messages are sent

if __name__ == "__main__":
    topic = "unconfirmed_transactions"
    produce_fake_data(topic, interval=1)  # Send a message every second
