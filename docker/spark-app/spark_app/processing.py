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

        for candidate in time_candidates:
            if candidate in available_columns:
                chosen_time_col = col(candidate)
                break

        if chosen_time_col is None:
            raise ValueError(f"❌ No suitable time-related column found! Available columns: {available_columns}")

        enriched = batch_df \
            .withColumn("block_age_seconds", (current_timestamp().cast("long") - chosen_time_col)) \
            .withColumn("tx_density", col("tx_count") / 1000.0) \
            .withColumn("block_bucket", spark_hash("id") % 100)

        feature_df = enriched.select(
            "id", "height", chosen_time_col.alias("time"), "tx_count",
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
