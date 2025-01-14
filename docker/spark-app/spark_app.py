from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("SimpleApp").getOrCreate()

data = [("Hello, PySpark!",)]
df = spark.createDataFrame(data, ["message"])

df.show()
spark.stop()
