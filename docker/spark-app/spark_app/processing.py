import math

import spark_app.config as config
import spark_app.logging_utils as logging_utils

from pyspark.sql.functions import (
    to_json, struct, size, col, expr, udf,
    array_distinct, hash as spark_hash,
    unix_timestamp, current_timestamp
)
from pyspark.sql.types import DoubleType

LOGGER = logging_utils.init_logger()

# UDF to compute entropy over address lists
def entropy(addr_list):
    if not addr_list:
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

    try:
        # Flatten the nested "x" struct
        txs = batch_df.selectExpr("x.*")

        # Extract reusable address arrays
        txs = txs \
            .withColumn("input_addrs", expr("transform(inputs, x -> x.prev_out.addr)")) \
            .withColumn("output_addrs", expr("transform(out, x -> x.addr)"))

        # Enrich with derived features
        enriched = txs \
            .withColumn("num_inputs", size("inputs")) \
            .withColumn("num_outputs", size("out")) \
            .withColumn("input_value_sum", expr("aggregate(transform(inputs, x -> x.prev_out.value), 0L, (acc, x) -> acc + x)")) \
            .withColumn("output_value_sum", expr("aggregate(transform(out, x -> x.value), 0L, (acc, x) -> acc + x)")) \
            .withColumn("fee", col("input_value_sum") - col("output_value_sum")) \
            .withColumn("fee_rate", expr("CASE WHEN size > 0 THEN fee / size ELSE NULL END")) \
            .withColumn("input_entropy", entropy_udf("input_addrs")) \
            .withColumn("output_entropy", entropy_udf("output_addrs")) \
            .withColumn("distinct_input_addrs", size(array_distinct("input_addrs"))) \
            .withColumn("distinct_output_addrs", size(array_distinct("output_addrs"))) \
            .withColumn("relayed_by_bucket", spark_hash("relayed_by") % 100)

        # Select relevant features only
        feature_df = enriched.select(
            "tx_index", "time", "size", "vin_sz", "vout_sz",
            "input_value_sum", "output_value_sum", "fee", "fee_rate",
            "input_entropy", "output_entropy",
            "distinct_input_addrs", "distinct_output_addrs",
            "relayed_by_bucket"
        )

        # Output to Kafka topic as JSON
        feature_df.select(to_json(struct("*")).alias("value")) \
            .write \
            .format("kafka") \
            .option("kafka.bootstrap.servers", config.KAFKA_BOOTSTRAP) \
            .option("topic", config.TARGET_TOPIC_UNCONFIRMED) \
            .save()

    except Exception as e:
        LOGGER.error(f"🔥 Error processing unconfirmed batch {batch_id}: {e}", exc_info=True)

def process_confirmed(batch_df, batch_id):
    if batch_df.isEmpty():
        LOGGER.info(f"📭 Skipping empty confirmed batch {batch_id}")
        return

    LOGGER.info(f"📦 Processing confirmed block batch {batch_id}")

    try:
        # Fallback priority: try these columns in order
        time_candidates = ["timestamp", "time", "block_time", "created_at"]

        available_columns = batch_df.columns
        chosen_time_col = None
        chosen_time_name = None

        for candidate in time_candidates:
            if candidate in available_columns:
                chosen_time_col = col(candidate)
                chosen_time_name = candidate
                break

        if chosen_time_col is None:
            raise ValueError(f"❌ No suitable time-related column found! Available columns: {available_columns}")

        enriched = batch_df \
            .withColumn("block_age_seconds", (current_timestamp().cast("long") - chosen_time_col)) \
            .withColumn("tx_density", col("tx_count") / 1000.0) \
            .withColumn("block_bucket", spark_hash("id") % 100)

        feature_df = enriched.select(
            "id", "height", chosen_time_name, "tx_count",
            "block_age_seconds", "tx_density", "block_bucket"
        )

        feature_df.select(to_json(struct("*")).alias("value")) \
            .write \
            .format("kafka") \
            .option("kafka.bootstrap.servers", config.KAFKA_BOOTSTRAP) \
            .option("topic", config.TARGET_TOPIC_CONFIRMED) \
            .save()

    except Exception as e:
        LOGGER.error(f"🔥 Error processing confirmed batch {batch_id}: {e}", exc_info=True)
