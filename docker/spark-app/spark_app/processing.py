from pyspark.sql.functions import (
    to_json, struct, size, col, expr, countDistinct, udf,
    array_distinct, hash as spark_hash
)

from pyspark.sql.types import DoubleType
from .config import KAFKA_BOOTSTRAP, TARGET_TOPIC_CONFIRMED, TARGET_TOPIC_UNCONFIRMED
from .logging_utils import init_logger
import math

LOGGER = init_logger()

# UDF to compute entropy over address lists
def entropy(addr_list):
    if not addr_list or len(addr_list) == 0:
        return 0.0
    freq = {}
    for addr in addr_list:
        freq[addr] = freq.get(addr, 0) + 1
    total = len(addr_list)
    return -sum((c / total) * math.log2(c / total) for c in freq.values())

entropy_udf = udf(entropy, DoubleType())


def process_unconfirmed(batch_df, batch_id):
    if batch_df.isEmpty():
        LOGGER.info(f"📭 Skipping empty unconfirmed batch {batch_id}")
        return

    LOGGER.info(f"🧾 Processing unconfirmed batch {batch_id}")

    # Flatten the nested "x" struct
    txs = batch_df.selectExpr("x.*")

    # Enrich with derived features
    enriched = txs \
        .withColumn("num_inputs", size("inputs")) \
        .withColumn("num_outputs", size("out")) \
        .withColumn("input_value_sum", expr("aggregate(inputs.prev_out.value, 0L, (acc, x) -> acc + x)")) \
        .withColumn("output_value_sum", expr("aggregate(out.value, 0L, (acc, x) -> acc + x)")) \
        .withColumn("fee", col("input_value_sum") - col("output_value_sum")) \
        .withColumn("fee_rate", col("fee") / col("size")) \
        .withColumn("input_entropy", entropy_udf("inputs.prev_out.addr")) \
        .withColumn("output_entropy", entropy_udf("out.addr")) \
        .withColumn(
            "distinct_input_addrs",
            size(array_distinct(expr("transform(inputs, x -> x.prev_out.addr)")))
        ) \
        .withColumn(
            "distinct_output_addrs",
            size(array_distinct(expr("transform(out, x -> x.addr)")))
        ) \
        .withColumn("relayed_by_bucket", spark_hash("relayed_by") % 100)

    # Select only relevant features for Kafka output
    feature_df = enriched.select(
        "tx_index", "time",
        "num_inputs", "num_outputs",
        "input_value_sum", "output_value_sum",
        "fee", "fee_rate",
        "input_entropy", "output_entropy",
        "distinct_input_addrs", "distinct_output_addrs",
        "relayed_by_bucket"
    )

    # Output to Kafka topic as JSON messages
    feature_df.select(to_json(struct("*")).alias("value")) \
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
