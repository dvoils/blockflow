import os
import logging

def init_logger():
    log_dir = "/mnt/spark/logs"
    log_file = os.path.join(log_dir, "spark-unified.log")

    try:
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
    except PermissionError:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    logger = logging.getLogger("UnifiedKafkaStreamApp")
    if not logger.hasHandlers():
        logger.addHandler(logging.StreamHandler())
    return logger
