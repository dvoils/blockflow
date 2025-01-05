from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, sum
from pyspark.sql.types import StructType, StructField, StringType, LongType

# Define the schema of the Kafka messages
transaction_schema = StructType([
    StructField("hash", StringType(), True),
    StructField("tx_index", LongType(), True),
    StructField("time", LongType(), True),
    StructField("inputs", StringType(), True),
    StructField("outputs", StructType([
        StructField("output_address", StringType(), True),
        StructField("output_value", LongType(), True)
    ]), True)
])

# Initialize Spark session
spark = SparkSession.builder \
    .appName("BlockchainProcessorMVP") \
    .getOrCreate()

# Read data from Kafka topic
raw_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "blockchain.raw") \
    .option("startingOffsets", "latest") \
    .load()

# Extract value and parse JSON
parsed_stream = raw_stream.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), transaction_schema).alias("data")) \
    .select("data.*")

# Filter transactions with high output values
filtered_transactions = parsed_stream \
    .select(col("outputs.output_address"), col("outputs.output_value")) \
    .where(col("outputs.output_value") > 100000000)  # 1 BTC = 100,000,000 satoshis

# Aggregate: Total transaction value per output address
aggregated_transactions = filtered_transactions \
    .groupBy("output_address") \
    .agg(sum("output_value").alias("total_value"))

# Write results to another Kafka topic
query = aggregated_transactions.writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("topic", "blockchain.processed") \
    .option("checkpointLocation", "/tmp/spark-checkpoints/blockchain-processor") \
    .outputMode("update") \
    .start()

# Wait for termination
query.awaitTermination()
