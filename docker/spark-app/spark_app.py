import time
import logging
from pyspark.sql import SparkSession
from signal import signal, SIGINT

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Graceful termination setup
keep_running = True

def handle_signal(signal_received, frame):
    global keep_running
    logger.info("Termination signal received. Stopping the application...")
    keep_running = False

signal(SIGINT, handle_signal)

# Create a Spark session
spark = SparkSession.builder.appName("SimpleApp").getOrCreate()

try:
    while keep_running:
        # Create and display a DataFrame
        data = [("Hello, PySpark!",)]
        df = spark.createDataFrame(data, ["message"])
        df.show()

        # Log the iteration
        logger.info("Iteration completed. Sleeping for 10 seconds...")

        # Wait before the next iteration
        time.sleep(10)
except Exception as e:
    logger.error("An error occurred", exc_info=e)
    raise
finally:
    # Stop the Spark session when exiting
    logger.info("Stopping the Spark session.")
    spark.stop()