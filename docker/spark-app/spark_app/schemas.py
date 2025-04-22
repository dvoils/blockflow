from pyspark.sql.types import *

unconfirmed_schema = StructType([
    StructField("op", StringType(), True),
    StructField("x", StructType([
        StructField("lock_time", IntegerType(), True),
        StructField("ver", IntegerType(), True),
        StructField("size", IntegerType(), True),
        StructField("inputs", ArrayType(
            StructType([
                StructField("sequence", LongType(), True),
                StructField("prev_out", StructType([
                    StructField("spent", BooleanType(), True),
                    StructField("tx_index", LongType(), True),
                    StructField("type", IntegerType(), True),
                    StructField("addr", StringType(), True),
                    StructField("value", LongType(), True),
                    StructField("n", IntegerType(), True),
                    StructField("script", StringType(), True)
                ]), True),
                StructField("script", StringType(), True)
            ])), True),
        StructField("time", LongType(), True),
        StructField("tx_index", LongType(), True),
        StructField("vin_sz", IntegerType(), True),
        StructField("hash", StringType(), True),
        StructField("vout_sz", IntegerType(), True),
        StructField("relayed_by", StringType(), True),
        StructField("out", ArrayType(
            StructType([
                StructField("spent", BooleanType(), True),
                StructField("tx_index", LongType(), True),
                StructField("type", IntegerType(), True),
                StructField("addr", StringType(), True),
                StructField("value", LongType(), True),
                StructField("n", IntegerType(), True),
                StructField("script", StringType(), True)
            ])), True)
    ]), True)
])

confirmed_schema = StructType([
    StructField("hash", StringType(), True),
    StructField("ver", IntegerType(), True),
    StructField("prev_block", StringType(), True),
    StructField("mrkl_root", StringType(), True),
    StructField("time", LongType(), True),
    StructField("bits", IntegerType(), True),
    StructField("fee", LongType(), True),
    StructField("nonce", IntegerType(), True),
    StructField("n_tx", IntegerType(), True),
    StructField("size", IntegerType(), True),
    StructField("block_index", LongType(), True),
    StructField("main_chain", BooleanType(), True),
    StructField("height", LongType(), True),
    StructField("weight", LongType(), True),
    StructField("tx", ArrayType(StringType()), True)
])
