from pyspark.sql.functions import to_json, struct
from .config import KAFKA_BOOTSTRAP, TARGET_TOPIC_CONFIRMED, TARGET_TOPIC_UNCONFIRMED
from .logging_utils import init_logger

LOGGER = init_logger()

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
