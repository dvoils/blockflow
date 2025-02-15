import os
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# ✅ Configure Log4j for structured logging
log4jLogger = SparkSession.builder.getOrCreate()._jvm.org.apache.log4j
LOGGER = log4jLogger.LogManager.getLogger("KafkaUnconfirmedTransactionsReader")

# ✅ Create a Spark session
spark = SparkSession.builder \
    .appName("KafkaUnconfirmedTransactionsReader") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .getOrCreate()

LOGGER.info("Spark session started.")

# ✅ Define Kafka source with fully qualified domain name for the Kafka service
try:
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka-broker.kafka.svc.cluster.local:9092") \
        .option("subscribe", "unconfirmed_transactions") \
        .option("startingOffsets", "earliest") \
        .load()
    
    LOGGER.info("Connected to Kafka topic: unconfirmed_transactions")
except Exception as e:
    LOGGER.error(f"Failed to connect to Kafka: {e}", exc_info=True)
    raise e

# ✅ Select the `value` column and cast it to STRING
messages_df = kafka_df.selectExpr("CAST(value AS STRING)")

# ✅ Log each batch processing step
def log_batch(batch_df, batch_id):
    LOGGER.info(f"Processing batch {batch_id}")

    messages = batch_df.collect()
    for message in messages:
        try:
            log_message = json.loads(message["value"])  # Convert JSON to dict
            LOGGER.info(f"Transaction: {log_message}")  # Log structured JSON
        except Exception as e:
            LOGGER.error(f"Failed to process message: {e}", exc_info=True)

# ✅ Ensure the checkpoint directory exists
checkpoint_location = "/mnt/spark/checkpoints/kafka_unconfirmed_transactions_reader"

# ✅ Write the streaming data to the console and log messages
query = messages_df.writeStream \
    .outputMode("append") \
    .foreachBatch(log_batch) \
    .option("checkpointLocation", checkpoint_location) \
    .start()

try:
    LOGGER.info("Streaming query started.")
    query.awaitTermination()
except Exception as e:
    LOGGER.error(f"Streaming query failed: {e}", exc_info=True)
