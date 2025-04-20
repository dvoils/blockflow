from unittest.mock import patch
from pyspark.sql import Row
from spark_app import process_unconfirmed, process_confirmed

@patch("pyspark.sql.DataFrameWriter.save")
def test_process_unconfirmed_happy_path(mock_save, spark, tmp_path):
    data = [Row(op="utx", x={
        "lock_time": 0, "ver": 1, "size": 250, "time": 12345678,
        "tx_index": 9999, "vin_sz": 1, "vout_sz": 2, "hash": "abcd", "relayed_by": "1.2.3.4",
        "inputs": [], "out": []
    })]
    df = spark.createDataFrame(data)
    df.write.json(str(tmp_path / "output_unconfirmed"), mode="overwrite")

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
