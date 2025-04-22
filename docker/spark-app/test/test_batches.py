from unittest.mock import patch
from pyspark.sql import Row
from pyspark.sql.types import *

from spark_app.processing import process_unconfirmed, process_confirmed

@patch("pyspark.sql.DataFrameWriter.save")
def test_process_unconfirmed_happy_path(mock_save, spark, tmp_path):
    # Define nested prev_out struct
    prev_out_schema = StructType([
        StructField("spent", BooleanType(), True),
        StructField("tx_index", LongType(), True),
        StructField("type", IntegerType(), True),
        StructField("addr", StringType(), True),
        StructField("value", LongType(), True),
        StructField("n", IntegerType(), True),
        StructField("script", StringType(), True)
    ])

    # Define input struct
    input_schema = StructType([
        StructField("sequence", LongType(), True),
        StructField("prev_out", prev_out_schema, True),
        StructField("script", StringType(), True)
    ])

    # Define out struct
    out_schema = StructType([
        StructField("spent", BooleanType(), True),
        StructField("tx_index", LongType(), True),
        StructField("type", IntegerType(), True),
        StructField("addr", StringType(), True),
        StructField("value", LongType(), True),
        StructField("n", IntegerType(), True),
        StructField("script", StringType(), True)
    ])

    x_schema = StructType([
        StructField("lock_time", IntegerType(), True),
        StructField("ver", IntegerType(), True),
        StructField("size", IntegerType(), True),
        StructField("inputs", ArrayType(input_schema), True),
        StructField("time", LongType(), True),
        StructField("tx_index", LongType(), True),
        StructField("vin_sz", IntegerType(), True),
        StructField("hash", StringType(), True),
        StructField("vout_sz", IntegerType(), True),
        StructField("relayed_by", StringType(), True),
        StructField("out", ArrayType(out_schema), True)
    ])

    schema = StructType([
        StructField("op", StringType(), True),
        StructField("x", x_schema, True),
    ])

    data = [{
        "op": "utx",
        "x": {
            "lock_time": 0,
            "ver": 1,
            "size": 250,
            "inputs": [{
                "sequence": 123456,
                "prev_out": {
                    "spent": True,
                    "tx_index": 8888,
                    "type": 1,
                    "addr": "1Example",
                    "value": 1000000,
                    "n": 0,
                    "script": "abc"
                },
                "script": "some-script"
            }],
            "time": 12345678,
            "tx_index": 9999,
            "vin_sz": 1,
            "hash": "abcd",
            "vout_sz": 2,
            "relayed_by": "1.2.3.4",
            "out": []
        }
    }]

    df = spark.createDataFrame(data, schema=schema)

    process_unconfirmed(df, batch_id=0)
    mock_save.assert_called_once()


@patch("pyspark.sql.DataFrameWriter.save")
def test_process_confirmed_happy_path(mock_save, spark, tmp_path):
    data = [Row(hash="0000abcd", ver=1, prev_block="0000aaaa", mrkl_root="root", time=12345678,
                bits=400000000, fee=123456, nonce=123, n_tx=12, size=400000, block_index=1234,
                main_chain=True, height=99999, weight=3999999, tx=["tx1", "tx2"])]
    df = spark.createDataFrame(data)
    df.write.json(str(tmp_path / "output_confirmed"), mode="overwrite")

    process_confirmed(df, batch_id=1)
    mock_save.assert_called_once()
