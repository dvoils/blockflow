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

# Specify a local persistent checkpoint location
checkpoint_location = "/mnt/spark/checkpoints/kafka_unconfirmed_transactions_reader"

# Write the streaming data to the console with checkpointing
query = messages_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()
# TODO: add checkpoint to the above writestream
# .option("checkpointLocation", checkpoint_location) \

try:
    # Wait for the query to terminate
    query.awaitTermination()
except Exception as e:
    print(f"Streaming query failed: {e}")
