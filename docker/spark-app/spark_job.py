from pyspark.sql import SparkSession

# Create a Spark session
spark = SparkSession.builder.appName("SimpleApp").getOrCreate()

# Create a DataFrame
data = [("Hello, PySpark!",)]
df = spark.createDataFrame(data, ["message"])

# Show the DataFrame
df.show()

# Stop the Spark session
spark.stop()