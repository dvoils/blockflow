import os
import json
import logging
import traceback
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_json, struct
from pyspark.sql.types import *

# Config
KAFKA_BOOTSTRAP = "kafka-broker.kafka.svc.cluster.local:9092"
TOPIC_UNCONFIRMED = "unconfirmed_transactions"
TOPIC_CONFIRMED = "confirmed_blocks"
TARGET_TOPIC_UNCONFIRMED = "processed_transactions"
TARGET_TOPIC_CONFIRMED = "processed_confirmed_blocks"

# Logging
log_dir = "/mnt/spark/logs"
log_file = os.path.join(log_dir, "spark-unified.log")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger("UnifiedKafkaStreamApp")
LOGGER.info("✅ Unified Spark Streaming App starting...")

# Spark Session
spark = SparkSession.builder \
    .appName("UnifiedKafkaStreamApp") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .getOrCreate()
LOGGER.info("🚀 Spark session started.")

# Kafka Source
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", f"{TOPIC_UNCONFIRMED},{TOPIC_CONFIRMED}") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()
LOGGER.info("🔗 Subscribed to Kafka topics.")

# ========== Unconfirmed Transactions Schema ==========
unconfirmed_schema = StructType([
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

# ========== Confirmed Blocks Schema ==========
confirmed_schema = StructType([
    StructField("hash", StringType(), True),
    StructField("ver", IntegerType(), True),
    StructField("prev_block", StringType(), True),
    StructField("mrkl_root", StringType(), True),
    StructField("time", LongType(), True),
    StructField("bits", IntegerType(), True),
    StructField("fee", LongType(), True),
    StructField("nonce", IntegerType(), True),
    StructField("n_tx", IntegerType(), True),
    StructField("size", IntegerType(), True),
    StructField("block_index", LongType(), True),
    StructField("main_chain", BooleanType(), True),
    StructField("height", LongType(), True),
    StructField("weight", LongType(), True),
    StructField("tx", ArrayType(StringType()), True)
])

# Parse value as STRING
raw_values = kafka_df.selectExpr("CAST(value AS STRING) as json_data")

# ========== Routing and Parsing ==========
unconfirmed_df = raw_values \
    .filter(col("json_data").contains('"op":"utx"')) \
    .select(from_json(col("json_data"), unconfirmed_schema).alias("data")) \
    .filter(col("data").isNotNull()) \
    .select("data.*")

# ========== Confirmed Blocks Parsing with Schema Validation ==========
INVALID_TOPIC_CONFIRMED = "invalid_confirmed_blocks"

try:
    confirmed_attempt = raw_values \
        .filter(col("json_data").contains('"height"')) \
        .select(from_json(col("json_data"), confirmed_schema).alias("parsed"), col("json_data").alias("raw_json")) \
        .withColumn("schema_valid", col("parsed").isNotNull())

    confirmed_df = confirmed_attempt \
        .filter(col("parsed").isNotNull()) \
        .selectExpr("parsed.*", "schema_valid")

    # Send invalid records to Kafka
    invalid_confirmed_df = confirmed_attempt \
        .filter(col("parsed").isNull()) \
        .selectExpr("CAST(raw_json AS STRING) AS value")

    invalid_query = invalid_confirmed_df.writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("topic", INVALID_TOPIC_CONFIRMED) \
        .option("checkpointLocation", "/mnt/spark/checkpoints/invalid_confirmed_kafka") \
        .outputMode("append") \
        .start()

    LOGGER.info("✅ Parsed confirmed_df with validation; streaming invalid records to Kafka topic.")
except Exception as e:
    LOGGER.error("❌ Failed parsing confirmed_df: %s", str(e))
    LOGGER.error(traceback.format_exc())
    raise

# ========== Process Batch Logic ==========
def process_unconfirmed(batch_df, batch_id):
    if batch_df.isEmpty():
        LOGGER.info(f"📭 Skipping empty unconfirmed batch {batch_id}")
        return
    LOGGER.info(f"🧾 Processing unconfirmed batch {batch_id}")
    batch_df.select(to_json(struct("*")).alias("value")) \
        .write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("topic", TARGET_TOPIC_UNCONFIRMED) \
        .save()

def process_confirmed(batch_df, batch_id):
    if batch_df.isEmpty():
        LOGGER.info(f"📭 Skipping empty confirmed batch {batch_id}")
        return
    LOGGER.info(f"📦 Processing confirmed block batch {batch_id}")
    batch_df.select(to_json(struct("*")).alias("value")) \
        .write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("topic", TARGET_TOPIC_CONFIRMED) \
        .save()

# ========== Write Streams ==========
checkpoint_base = "/mnt/spark/checkpoints"

query1 = unconfirmed_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_unconfirmed) \
    .option("checkpointLocation", f"{checkpoint_base}/unconfirmed") \
    .start()

query2 = confirmed_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_confirmed) \
    .option("checkpointLocation", f"{checkpoint_base}/confirmed") \
    .start()

LOGGER.info("🟢 Unified stream queries started.")

query1.awaitTermination()
query2.awaitTermination()
invalid_query.awaitTermination()

