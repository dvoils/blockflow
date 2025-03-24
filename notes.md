

kubectl delete deployment spark-streaming-app -n spark
kubectl delete pods --all -n spark

kubectl delete deployment ingest-app -n kafka

kubectl delete configmap spark-config -n spark


kafka-console-consumer.sh --bootstrap-server kafka-broker-7fb7f7bb66-c5ppm:9092 --topic unconfirmed_transactions --from-beginning

kubectl exec -it spark-streaming-app-xxxxxx -c spark-streaming-app -n spark -- tail -f /mnt/spark/logs/spark-app.log
kubectl exec -it spark-streaming-app-7d8f6d56d8-jgj8x -c spark-streaming-app -n spark -- tail -f /mnt/spark/logs/spark-app.log


kubectl delete pod -n spark -l app=spark-streaming-app

kubectl logs spark-streaming-app-7bb695b759-hv6qn -n spark
kubectl describe pod spark-streaming-app-7bb695b759-hv6qn -n spark

kubectl logs -f spark-streaming-app-7d8f6d56d8-kk8bv -c fluent-bit -n spark
kubectl exec -it spark-streaming-app-7bb695b759-hv6qn -n spark -- bash
kubectl describe pod spark-streaming-app-7d8f6d56d8-tr8zk -n spark




kubectl describe node minikube


docker run -it --user root spark-with-kafka:3.4.0 bash
docker run -it --user root spark-app:latest bash


kubectl delete deployment spark-app -n spark
kubectl delete pods --all -n kafka




Your **Spark Structured Streaming app** is well-structured, but given the Kafka offset reset issue you encountered, there are a few improvements you can make to **increase resilience** and **avoid data loss**. Let's go over the key points:

---

## **🔍 Review of Your Spark Streaming App**
### ✅ **Good Aspects**
1. **Proper Kafka Connection**  
   - You're using `.option("subscribe", "unconfirmed_transactions")` to listen to the topic.  
   - `startingOffsets="earliest"` ensures no data is missed **if the topic is new**.

2. **Well-Defined Schema**  
   - The transaction schema (`tx_schema`) is well-defined, preventing schema-related errors.

3. **Logging for Debugging**  
   - Logging at each stage helps track batch execution and potential errors.

4. **Batch Processing via `foreachBatch`**  
   - This ensures each micro-batch can be handled independently.

5. **Checkpointing Enabled**  
   - You're using a checkpoint directory (`/mnt/spark/checkpoints/kafka_unconfirmed_transactions_reader`), which helps **track offsets** between runs.

---

## **⚠️ Issues and Areas for Improvement**
### **1️⃣ Kafka Offsets Issue: Handling Data Loss**
#### **Problem**  
Your logs showed:
```log
Partition unconfirmed_transactions-0's offset was changed from 121068 to 259, some data may have been missed.
```
- Kafka **deleted older messages** due to retention settings (`retention.ms` expired).
- Spark **expected old offsets**, but Kafka had already purged them.
- This caused **Spark to crash** because it couldn’t find the expected offsets.

#### **Solution**
To **prevent crashes** when old messages are deleted, add:
```python
.option("failOnDataLoss", "false")
```
This tells Spark to **continue from the latest available offset** instead of failing.

✅ **Fix: Update Kafka Read Configuration**
```python
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-broker.kafka.svc.cluster.local:9092") \
    .option("subscribe", "unconfirmed_transactions") \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \  # ✅ Prevents job crashes due to offset loss
    .load()
```
---
### **2️⃣ Ensure Kafka Retention is Sufficient**
If you **don’t want data loss**, increase Kafka **retention time**:
```sh
kafka-configs.sh --bootstrap-server kafka-broker:9092 \
                 --entity-type topics --entity-name unconfirmed_transactions \
                 --alter --add-config retention.ms=86400000  # 24 hours
```
- **retention.ms** = **86400000ms (24 hours)** keeps messages longer, reducing Spark crashes due to offset loss.
- Consider increasing even more if Spark **lags behind Kafka**.

---

### **3️⃣ Handle Schema Evolution (Optional)**
- If Kafka messages **change structure** over time, Spark **will fail**.
- Use `.option("schemaEvolutionMode", "addOrIgnore")`:
```python
.option("schemaEvolutionMode", "addOrIgnore")
```
This allows Spark to **handle new fields gracefully**.

---
### **4️⃣ Optimize `.collect()` for Large Datasets**
```python
rows = batch_df.collect()  # ⚠️ This brings all rows to the driver! Not scalable.
```
- If **too many transactions arrive**, this will cause **Out of Memory (OOM)** issues.
- Instead, **iterate directly** over the DataFrame:
```python
def process_batch(batch_df, batch_id):
    start_time = datetime.now()
    LOGGER.info(f"🛠 Processing batch {batch_id}")

    for row in batch_df.toLocalIterator():  # ✅ Streams row-by-row
        try:
            transaction_hash = row.x.hash if row.x and row.x.hash else "N/A"
            LOGGER.info(f"📦 Transaction hash: {transaction_hash}")
        except Exception as e:
            LOGGER.error(f"⚠️ Error processing row: {e}", exc_info=True)

    duration = (datetime.now() - start_time).total_seconds()
    LOGGER.info(f"⏱ Batch {batch_id} processed in {duration:.2f} seconds.")
```
✅ **Why?**
- `collect()` loads **all data into memory**, which fails for large datasets.
- `toLocalIterator()` **processes one row at a time**, reducing memory usage.

---

### **5️⃣ Improve Checkpointing for Faster Recovery**
You're already using:
```python
.option("checkpointLocation", "/mnt/spark/checkpoints/kafka_unconfirmed_transactions_reader")
```
- If **Spark restarts**, it resumes from the last committed **offsets**.
- If you want **better fault tolerance**, store it in a **distributed storage system** (e.g., HDFS, S3, GCS).

✅ **Use S3 (or equivalent) for resilience**
```python
.option("checkpointLocation", "s3a://your-bucket/spark-checkpoints/")
```
- This ensures **checkpoints persist** even if Spark crashes.

---

## **🚀 Final Optimized Spark Streaming Code**
```python
import os
import json
import logging
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType, BooleanType, LongType

# ✅ Ensure logging directory exists
log_dir = "/mnt/spark/logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, "spark-app.log"),
                    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger("KafkaUnconfirmedTransactionsReader")

LOGGER.info("✅ Python logging initialized.")

# ✅ Create Spark session
spark = SparkSession.builder \
    .appName("KafkaUnconfirmedTransactionsReader") \
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .getOrCreate()

LOGGER.info("🚀 Spark session started.")

# ✅ Kafka source
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka-broker.kafka.svc.cluster.local:9092") \
    .option("subscribe", "unconfirmed_transactions") \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \  # ✅ Prevents crashes due to offset loss
    .load()

LOGGER.info("🔗 Connected to Kafka topic: unconfirmed_transactions")

# ✅ Define schema
tx_schema = StructType([...])  # Same as before

# ✅ Parse Kafka messages
messages_df = kafka_df.selectExpr("CAST(value AS STRING) as json_data") \
    .select(from_json(col("json_data"), tx_schema).alias("data")) \
    .select("data.*")


# ✅ Process batches efficiently
def process_batch(batch_df, batch_id):
    start_time = datetime.now()
    LOGGER.info(f"🛠 Processing batch {batch_id}")

    for row in batch_df.toLocalIterator():  # ✅ Streams rows to avoid memory issues
        try:
            transaction_hash = row.x.hash if row.x and row.x.hash else "N/A"
            LOGGER.info(f"📦 Transaction hash: {transaction_hash}")
        except Exception as e:
            LOGGER.error(f"⚠️ Error processing row: {e}", exc_info=True)

    duration = (datetime.now() - start_time).total_seconds()
    LOGGER.info(f"⏱ Batch {batch_id} processed in {duration:.2f} seconds.")

# ✅ Start streaming
checkpoint_location = "s3a://your-bucket/spark-checkpoints/"  # ✅ Improved checkpointing

query = messages_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_batch) \
    .option("checkpointLocation", checkpoint_location) \
    .start()

LOGGER.info("🟢 Streaming query started.")
query.awaitTermination()
```

---

## **🚀 Summary of Fixes**
| **Issue**  | **Fix** |
|------------|--------|
| **Kafka deleting old messages before Spark reads them** | **Increase `retention.ms`** in Kafka |
| **Spark failing due to missing offsets** | **Add `.option("failOnDataLoss", "false")`** |
| **Memory issues with `.collect()`** | **Use `toLocalIterator()` instead** |
| **Offset tracking lost on restart** | **Use checkpointing (`s3a://` or HDFS)** |

---

## **💡 Next Steps**
1. ✅ **Test the updated Spark job** and check if **offset errors disappear**.
2. ✅ **Monitor Kafka logs** to confirm retention settings.
3. ✅ **Ensure Kafka retention (`retention.ms`) is long enough** for Spark to process events.

**Let me know how it goes or if you have any questions!** 🚀



kubectl get pod spark-app-8d9974b9d-mqsmx -n spark -o yaml

kubectl exec -it spark-app-8d9974b9d-mqsmx -n spark -- bash

spark-submit \
    --master k8s://https://192.168.49.2:8443 \
    --deploy-mode cluster \
    --conf spark.kubernetes.namespace=spark \
    --conf spark.kubernetes.container.image=spark-with-kafka:3.4.0 \
    --conf spark.executor.instances=2 \
    --conf spark.executor.memory=1g \
    --conf spark.executor.cores=1 \
    --conf spark.kubernetes.file.upload.path=file:///tmp/spark-upload \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.authenticate.caCertFile=/etc/ssl/certs/ca-certificates.crt \
    --conf spark.kubernetes.authenticate.submission.oauthToken=${K8S_TOKEN} \
    --conf spark.kubernetes.authenticate.caCertFile=/usr/local/share/ca-certificates/minikube-ca.crt \
    /opt/app/app.py




kubectl exec -it spark-app-8d9974b9d-hf2jq -n spark -- bash



Inside the container, the output confirms that your Minikube CA certificate has been successfully added to the JVM trust store

keytool -list -keystore /opt/java/openjdk/lib/security/cacerts -storepass changeit | grep -i minikube
Warning: use -cacerts option to access cacerts keystore
minikube-ca, Jan 20, 2025, trustedCertEntry, 




kubectl get serviceaccounts -n spark
kubectl get roles -n spark
kubectl get clusterroles
kubectl get clusterrolebindings



kubectl delete job spark-app-job -n spark


kubectl auth can-i create pods --as=system:serviceaccount:spark:spark -n spark
kubectl auth can-i get pods --as=system:serviceaccount:spark:spark -n spark
kubectl auth can-i get configmaps --as=system:serviceaccount:spark:spark -n spark



docker cp ~/.minikube/ca.crt 30afeebabdf6:/usr/local/share/ca-certificates/minikube-ca.crt
docker cp ~/.minikube/ca.key 30afeebabdf6:/usr/local/share/ca-certificates/minikube-ca.key
docker cp ~/.minikube/ca.pem 30afeebabdf6:/usr/local/share/ca-certificates/minikube-ca.pem

curl -k https://192.168.49.2:8443 \
     --header "Authorization: Bearer $K8S_TOKEN" \
     --cacert /usr/local/share/ca-certificates/minikube-ca.crt



curl -k https://192.168.49.2:8443 \
     --header "Authorization: Bearer $K8S_TOKEN" \
     --cacert /usr/local/share/ca-certificates/minikube-ca.crt

docker run -it spark-app:latest bash

K8S_TOKEN=$(kubectl get secret spark-token -n spark -o jsonpath='{.data.token}' | base64 --decode)

docker run -it --rm \
  -e K8S_TOKEN="${K8S_TOKEN}" \
  spark-app:latest bash


export K8S_TOKEN=$(kubectl get secret spark-token -n spark -o jsonpath='{.data.token}' | base64 --decode)



spark-submit \
    --master k8s://https://192.168.49.2:8443 \
    --deploy-mode cluster \
    --conf spark.kubernetes.namespace=spark \
    --conf spark.kubernetes.container.image=spark-with-kafka:3.4.0 \
    --conf spark.executor.instances=3 \
    --conf spark.executor.memory=2g \
    --conf spark.executor.cores=1 \
    --conf spark.kubernetes.file.upload.path=file:///tmp/spark-upload \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.authenticate.caCertFile=/etc/ssl/certs/ca-certificates.crt \
    --conf spark.kubernetes.authenticate.submission.oauthToken=${K8S_TOKEN} \
    --conf spark.kubernetes.authenticate.caCertFile=/usr/local/share/ca-certificates/minikube-ca.crt \
    /opt/app/app.py



1. Create service account and roles
kubectl create serviceaccount spark -n spark (maybe this is already done)
create role.yaml and apply
create rolebinding.yaml and apply

2. Manually Create a Service Account Token Secret
create spark-token.yaml and apply


docker build --no-cache -t spark-with-kafka:3.4.0 -f Dockerfile.base .
docker build --no-cache -t spark-app:latest .

openssl crl2pkcs7 -nocrl -certfile /etc/ssl/certs/ca-certificates.crt | openssl pkcs7 -print_certs -noout | grep kube






cat docker/ingest-app/Dockerfile
cat docker/ingest-app/ingest_app.py
cat docker/spark-app/Dockerfile
cat docker/spark-app/spark_app.py

cat kubernetes/kafka/*.yaml
cat kubernetes/spark-app/*.yaml

docker run -it --rm spark-app:latest bash
docker run -it --rm spark-with-kafka:3.4.0 bash

spark-submit /opt/app/app.py

docker rmi d188efcaf113
Error response from daemon: conflict: unable to delete d188efcaf113 (must be forced) - image is being used by stopped container 6e95f227fefc

docker ps -a

docker stop 6e95f227fefc


kubectl delete deployment spark-app -n spark

docker rmi d188efcaf113


# Delete Pod/Deployment
```bash
kubectl delete pod spark-driver-749fb8cb44-knqm7 -n spark
kubectl delete deployment spark-driver -n spark
kubectl delete job spark-app-job -n spark

```


kubectl rollout status deployment/ingest-app -n kafka

kubectl create serviceaccount spark -n spark

kubectl rollout restart deployment spark-driver -n spark


docker run -it spark-app:latest ls /opt/spark/bin/spark-submit
docker run -it spark-app:latest bash


kubectl exec -it <POD_NAME> -n spark -- /bin/bash

eval $(minikube docker-env)  # Ensure Minikube is using your local Docker
kubectl rollout restart deployment spark-driver -n spark

docker run -it --name spark-debug bitnami/spark:3.5.4 /bin/bash


kubectl describe pod spark-driver-749fb8cb44-89n8s -n spark


kubectl logs ingest-app-57cb7677f-qzc75 -n kafka --previous

kubectl logs spark-driver-749fb8cb44-89n8s -n spark

kubectl auth can-i patch services --as=system:serviceaccount:spark:spark -n spark

kubectl delete pod -n spark $(kubectl get pods -n spark | grep 'ContainerCannotRun' | awk '{print $1}')

kubectl get configmap -n spark

kubectl describe configmap spark-drv-66fa1c9441fc28ea-conf-map -n spark

kubectl delete configmap spark-drv-e0b3e8944201db0b-conf-map -n spark


/opt/bitnami/spark/bin/spark-submit \
spark-submit \
  --master local \
  --conf spark.jars.ivy=/nonexistent \
  --jars local:///opt/spark/jars/hadoop-aws-3.3.4.jar,local:///opt/spark/jars/aws-java-sdk-bundle-1.11.1026.jar \
  local:///opt/spark/app/spark_app.py


spark-submit \
  --master local \
  local:///opt/spark/app/spark_app.py