from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from spark_app.config import *
from spark_app.schemas import unconfirmed_schema, confirmed_schema
from spark_app.processing import process_unconfirmed, process_confirmed
from spark_app.logging_utils import init_logger

def main():
    LOGGER = init_logger()
    LOGGER.info("✅ Starting Spark App")

    spark = SparkSession.builder \
        .appName("UnifiedKafkaStreamApp") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("subscribe", f"{TOPIC_UNCONFIRMED},{TOPIC_CONFIRMED}") \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    raw_values = kafka_df.selectExpr("CAST(value AS STRING) as json_data")

    unconfirmed_df = raw_values \
        .filter(col("json_data").contains('"op":"utx"')) \
        .select(from_json(col("json_data"), unconfirmed_schema).alias("data")) \
        .filter(col("data").isNotNull()) \
        .select("data.*")

    confirmed_attempt = raw_values \
        .filter(col("json_data").contains('"height"')) \
        .select(from_json(col("json_data"), confirmed_schema).alias("parsed"), col("json_data").alias("raw_json")) \
        .withColumn("schema_valid", col("parsed").isNotNull())

    confirmed_df = confirmed_attempt \
        .filter(col("parsed").isNotNull()) \
        .selectExpr("parsed.*", "schema_valid")

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

    query1 = unconfirmed_df.writeStream \
        .outputMode("append") \
        .foreachBatch(process_unconfirmed) \
        .option("checkpointLocation", "/mnt/spark/checkpoints/unconfirmed") \
        .start()

    query2 = confirmed_df.writeStream \
        .outputMode("append") \
        .foreachBatch(process_confirmed) \
        .option("checkpointLocation", "/mnt/spark/checkpoints/confirmed") \
        .start()

    LOGGER.info("🟢 Stream processing started")
    query1.awaitTermination()
    query2.awaitTermination()
    invalid_query.awaitTermination()

if __name__ == "__main__":
    main()
