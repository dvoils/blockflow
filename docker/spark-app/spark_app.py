from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("MyApp") \
    .config("spark.jars.ivy", "/nonexistent") \
    .config("spark.jars", "local:///opt/spark/jars/hadoop-aws-3.3.4.jar,local:///opt/spark/jars/aws-java-sdk-bundle-1.11.1026.jar") \
    .getOrCreate()


# Create a Spark session
# spark = SparkSession.builder.appName("SimpleApp").getOrCreate()

# Create a DataFrame
data = [("Hello, PySpark!",)]
df = spark.createDataFrame(data, ["message"])

# Show the DataFrame
df.show()

# Stop the Spark session
spark.stop()
