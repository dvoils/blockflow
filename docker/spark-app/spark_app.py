from pyspark.sql import SparkSession

# Create a Spark session
spark = SparkSession.builder.appName("MinimalApp").getOrCreate()

# Create a dummy streaming DataFrame that generates rows at a constant rate
df = spark.readStream.format("rate").option("rowsPerSecond", 1).load()

# Write the streaming data to the console
query = df.writeStream.format("console").start()

# Wait for the streaming query to terminate
query.awaitTermination()
