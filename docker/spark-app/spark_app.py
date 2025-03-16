import os
import json
import logging
from datetime import datetime
from pyspark.sql.functions import to_json, struct
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType, BooleanType, LongType

TARGET_TOPIC = "processed_transactions"

# ✅ Ensure the log directory exists
log_dir = "/mnt/spark/logs"
log_file = os.path.join(log_dir, "spark-app.log")

os.makedirs(log_dir, exist_ok=True)

# ✅ Configure Python logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger("KafkaUnconfirmedTransactionsReader")
LOGGER.info("✅ Python logging initialized.")

# ✅ Create Spark session
spark = SparkSession.builder \
    .appName("KafkaUnconfirmedTransactionsReader") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .getOrCreate()

LOGGER.info("🚀 Spark session started.")

# ✅ Kafka source definition
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-broker.kafka.svc.cluster.local:9092") \
    .option("subscribe", "unconfirmed_transactions") \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \
    .option("schemaEvolutionMode", "addOrIgnore") \
    .load()

LOGGER.info("🔗 Connected to Kafka topic: unconfirmed_transactions")

# ✅ Define the correct PySpark schema as a StructType object
tx_schema = StructType([
    StructField("op", StringType(), True),
    StructField("x", StructType([
        StructField("lock_time", IntegerType(), True),
        StructField("ver", IntegerType(), True),
        StructField("size", IntegerType(), True),
        StructField("inputs", ArrayType(
            StructType([
                StructField("sequence", LongType(), True),
                StructField("prev_out", StructType([
                    StructField("spent", BooleanType(), True),
                    StructField("tx_index", LongType(), True),
                    StructField("type", IntegerType(), True),
                    StructField("addr", StringType(), True),
                    StructField("value", LongType(), True),
                    StructField("n", IntegerType(), True),
                    StructField("script", StringType(), True)
                ]), True),
                StructField("script", StringType(), True)
            ])), True),
        StructField("time", LongType(), True),
        StructField("tx_index", LongType(), True),
        StructField("vin_sz", IntegerType(), True),
        StructField("hash", StringType(), True),
        StructField("vout_sz", IntegerType(), True),
        StructField("relayed_by", StringType(), True),
        StructField("out", ArrayType(
            StructType([
                StructField("spent", BooleanType(), True),
                StructField("tx_index", LongType(), True),
                StructField("type", IntegerType(), True),
                StructField("addr", StringType(), True),
                StructField("value", LongType(), True),
                StructField("n", IntegerType(), True),
                StructField("script", StringType(), True)
            ])), True)
    ]), True)
])

# ✅ Parse Kafka messages (corrected)
# ✅ Corrected parsing
messages_df = kafka_df.selectExpr("CAST(value AS STRING) as json_data") \
    .select(from_json(col("json_data"), tx_schema).alias("data")) \
    .select("data.*")


def process_batch(batch_df, batch_id):
    start_time = datetime.now()
    LOGGER.info(f"🛠 Processing batch {batch_id}")

    if batch_df.isEmpty():
        LOGGER.info("🚫 Empty batch, skipping.")
        return

    # ✅ Prepare and write to Kafka topic inside Spark job
    batch_df \
        .select(to_json(struct("*")).alias("value")) \
        .write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka-broker.kafka.svc.cluster.local:9092") \
        .option("topic", TARGET_TOPIC) \
        .save()

    duration = (datetime.now() - start_time).total_seconds()
    LOGGER.info(f"✅ Batch {batch_id} written to Kafka in {duration:.2f} seconds.")

# ✅ Start streaming
checkpoint_location = "/mnt/spark/checkpoints/kafka_unconfirmed_transactions_reader"

query = messages_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_batch) \
    .option("checkpointLocation", checkpoint_location) \
    .start()

LOGGER.info("🟢 Streaming query started.")
query.awaitTermination()
