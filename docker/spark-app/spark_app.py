import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Create a Spark session
spark = SparkSession.builder \
    .appName("KafkaUnconfirmedTransactionsReader") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .getOrCreate()

# Define Kafka source with fully qualified domain name for the Kafka service
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-broker.kafka.svc.cluster.local:9092") \
    .option("subscribe", "unconfirmed_transactions") \
    .option("startingOffsets", "earliest") \
    .load()

# Select the `value` column and cast it to STRING
messages_df = kafka_df.selectExpr("CAST(value AS STRING)")

# Log each message
def log_batch(batch_df, batch_id):
    print(f"Processing batch {batch_id}")
    messages = batch_df.collect()
    for message in messages:
        print(f"Message: {message['value']}")  # Adjust 'value' key if needed

# Ensure the checkpoint directory exists
checkpoint_location = "/mnt/spark/checkpoints/kafka_unconfirmed_transactions_reader"

# Write the streaming data to the console and log messages
query = messages_df.writeStream \
    .outputMode("append") \
    .foreachBatch(log_batch) \
    .option("checkpointLocation", checkpoint_location) \
    .start()

try:
    # Wait for the query to terminate
    query.awaitTermination()
except Exception as e:
    print(f"Streaming query failed: {e}")