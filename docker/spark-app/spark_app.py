import os
import json
import logging
import traceback
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_json, struct, explode
from pyspark.sql.types import *

# Config
KAFKA_BOOTSTRAP = "kafka-broker.kafka.svc.cluster.local:9092"
TOPIC_UNCONFIRMED = "unconfirmed_transactions"
TOPIC_MEMPOOL = "mempool_blocks"
TARGET_TOPIC_UNCONFIRMED = "processed_transactions"
TARGET_TOPIC_MEMPOOL = "processed_mempool_blocks"

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
    .option("subscribe", f"{TOPIC_UNCONFIRMED},{TOPIC_MEMPOOL}") \
    .option("startingOffsets", "earliest") \
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

# ========== Mempool Blocks Schema ==========
mempool_schema = StructType([
    StructField("mempool-blocks", ArrayType(
        StructType([
            StructField("blockSize", IntegerType(), True),
            StructField("blockVSize", DoubleType(), True),
            StructField("nTx", IntegerType(), True),
            StructField("totalFees", IntegerType(), True),
            StructField("medianFee", DoubleType(), True),
            StructField("feeRange", ArrayType(DoubleType()), True)
        ])
    ))
])

# Parse value as STRING
raw_values = kafka_df.selectExpr("CAST(value AS STRING) as json_data")

# ========== Routing and Parsing ==========
unconfirmed_df = raw_values \
    .filter(col("json_data").contains('"op":"utx"')) \
    .select(from_json(col("json_data"), unconfirmed_schema).alias("data")) \
    .filter(col("data").isNotNull()) \
    .select("data.*")

# Protect mempool block parsing
try:
    mempool_df = raw_values \
        .filter(col("json_data").contains('"mempool-blocks"')) \
        .select(from_json(col("json_data"), mempool_schema).alias("data")) \
        .filter(col("data").isNotNull()) \
        .selectExpr("explode(data.`mempool-blocks`) as block") \
        .select("block.*")
    LOGGER.info("✅ Parsed mempool_df successfully.")
except Exception as e:
    LOGGER.error(f"❌ Failed parsing mempool_df: {e}")
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

def process_mempool(batch_df, batch_id):
    if batch_df.isEmpty():
        LOGGER.info(f"📭 Skipping empty mempool batch {batch_id}")
        return
    LOGGER.info(f"📊 Processing mempool batch {batch_id}")
    batch_df.select(to_json(struct("*")).alias("value")) \
        .write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("topic", TARGET_TOPIC_MEMPOOL) \
        .save()

# ========== Write Streams ==========
checkpoint_base = "/mnt/spark/checkpoints"

query1 = unconfirmed_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_unconfirmed) \
    .option("checkpointLocation", f"{checkpoint_base}/unconfirmed") \
    .start()

query2 = mempool_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_mempool) \
    .option("checkpointLocation", f"{checkpoint_base}/mempool") \
    .start()

LOGGER.info("🟢 Unified stream queries started.")

# Optional: Show raw values for debugging
# raw_values.writeStream \
#     .format("console") \
#     .option("truncate", False) \
#     .start()

query1.awaitTermination()
query2.awaitTermination()
