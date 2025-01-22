from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("KafkaSparkStreaming").getOrCreate()

# Read from Kafka
kafka_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "my-topic") \
    .load()

# Process the data
processed_df = kafka_df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

# Write the processed data to the console or a sink
query = processed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
