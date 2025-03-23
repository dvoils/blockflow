
# Debugging Workflow

Your current **Kafka debugging approach** is solid, but here are **some refinements** to avoid unnecessary noise in the logs and make debugging more efficient.

---

### **Issues With Your Current Approach**
1. **Console Consumers Keep Creating New Groups**  
   - Each time you run `kafka-console-consumer.sh`, a **new ephemeral consumer group** (`console-consumer-XXXXX`) is created.
   - These ephemeral groups **quickly leave** when you exit, leading to constant rebalancing (which floods logs).

2. **Unbounded Log Streaming (`--from-beginning`)**  
   - This reads **all past messages** every time, making it **harder to focus on new messages**.
   - Can cause **log spam** if your topic has a lot of old messages.

3. **Test Producer Pod is Ephemeral (`--rm`)**  
   - The test pod disappears after exit. If you need to send multiple test messages, you have to recreate it each time.

---

### **Improved Debugging Approach**
Here’s a **better** way to test Kafka in Kubernetes without overwhelming logs.

#### **Step 1: Create a Persistent Debugging Pod**
Instead of a one-off pod that disappears, create a **long-running debugging pod**:

```bash
kubectl run kafka-debugger \
  -n kafka \
  --image=wurstmeister/kafka \
  --restart=Never \
  -- sleep infinity
```

Then, exec into it when needed:
```bash
kubectl exec -it kafka-debugger -n kafka -- /bin/bash
```
✅ **Advantage**:  
- You can reuse this pod without recreating it every time.

---

#### **Step 2: Consume Messages Without Log Spam**
Instead of constantly replaying old messages, consume **only new messages**:

```bash
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-broker:9092 \
  --topic unconfirmed_transactions \
  --group kafka-debug-group
```
✅ **Advantage**:
- This consumer **stays in the same group** (`kafka-debug-group`), avoiding ephemeral groups.
- No **unnecessary rebalancing** spam.
- Reads only **new messages**, reducing log clutter.

---

#### **Step 3: Producing Test Messages**
Inside the same debugging pod, produce test messages:

```bash
/opt/kafka/bin/kafka-console-producer.sh \
  --broker-list kafka-broker:9092 \
  --topic unconfirmed_transactions
```
Then, type a message and press Enter:
```
{"txid": "abc123", "amount": 0.5, "currency": "BTC"}
```
✅ **Advantage**:
- Quickly verify if messages are ingested properly.

---

#### **Step 4: Debugging Live Ingest App Logs**
To monitor your `ingest_app` logs while debugging Kafka, use:
```bash
kubectl logs -f -n kafka ingest_app
```
If needed, restart the pod to reload Kafka consumers:
```bash
kubectl rollout restart deploy/ingest-app -n kafka
```

---

### **Summary of Improvements**
| **Old Method** | **New Method** |
|---------------|---------------|
| Creates a new test pod every time | Persistent pod (`kafka-debugger`) |
| Uses `--from-beginning` (replays all old messages) | Uses a **persistent consumer group** (`kafka-debug-group`) |
| Generates too many `console-consumer-XXXXX` groups | Reuses the same consumer group |
| Logs get spammed with rebalancing events | Reduces log clutter by stabilizing consumer group |

---

### **Final Debugging Workflow**
1. **Start a reusable debug pod**:  
   ```bash
   kubectl run kafka-debugger -n kafka --image=wurstmeister/kafka --restart=Never -- sleep infinity
   ```
2. **Exec into the pod**:  
   ```bash
   kubectl exec -it kafka-debugger -n kafka -- /bin/bash
   ```
3. **Consume only new messages**: 
   ```bash

   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-broker:9092 --topic unconfirmed_transactions --group kafka-debug-group
   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-broker:9092 --topic spark-logs --group kafka-debug-group
   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-broker:9092 --topic processed_transactions --group kafka-debug-group

   ```
4. **Produce test messages**:  
   ```bash
   /opt/kafka/bin/kafka-console-producer.sh --broker-list kafka-broker:9092 --topic unconfirmed_transactions
   ```
5. **Monitor `ingest_app` logs**:  
   ```bash
   kubectl logs -f -n kafka ingest_app
   ```

This approach keeps logs clean, stabilizes the Kafka consumer, and makes debugging much easier. 🚀

# Notes on Debugging

### **Analysis of the `ingest_app` Pod Logs**
The logs you posted primarily show **Kafka consumer group activity**, specifically:
- **Consumer group rebalancing**
- **Consumers joining and leaving**
- **Groups transitioning to an empty state (dead groups)**

---

### **What These Logs Indicate**
1. **Consumers are frequently joining and leaving**  
   - Multiple consumer groups (e.g., `console-consumer-42208`, `console-consumer-35600`, `console-consumer-50367`, etc.) are being created, but they are also quickly leaving or becoming empty.
   - Each time a consumer joins, Kafka creates a new generation for the group.
   - Soon after, the consumer leaves, triggering a rebalance.

2. **Rebalancing is happening very often**  
   - Every time a consumer disconnects, Kafka **rebalances** the group.
   - This is normal when consumers **stop unexpectedly** or when they are **short-lived** (e.g., temporary console consumers).

3. **Consumer groups are transitioning to DEAD state**  
   - Messages like:
     ```
     INFO [GroupMetadataManager brokerId=1] Group console-consumer-XXXX transitioned to Dead
     ```
     indicate that Kafka is **removing** consumer groups when they become empty.

---

### **Potential Causes**
Here are some possible reasons for this behavior:

#### **1. Temporary Kafka Console Consumers**
- If you are running `kafka-console-consumer.sh` manually for debugging, each invocation **creates a new ephemeral consumer group**, which then disappears after the session ends.
- These consumers show up in the logs as `console-consumer-XXXXX` groups, repeatedly joining and leaving.

  ✅ **Solution**:  
  - If you want to debug without polluting logs with temporary consumer groups, **use the same consumer group consistently**:
    ```bash
    /opt/kafka/bin/kafka-console-consumer.sh \
      --bootstrap-server kafka-broker:9092 \
      --topic unconfirmed_transactions \
      --group my-debug-group
    ```
  - This prevents Kafka from creating a new consumer group for each session.

---

#### **2. Consumers Shutting Down Too Quickly**
- If your application (`ingest_app`) is a consumer and is crashing or disconnecting too fast, you might see this pattern.

  ✅ **Solution**:  
  - Check **your consumer logs** for errors (timeouts, memory issues, crashes).
  - Ensure your consumers have proper **error handling and retry mechanisms**.

---

#### **3. Short Consumer Timeout Settings**
- If Kafka consumers are **taking too long** to poll messages, Kafka might assume they are dead and remove them from the group.
- Default **session timeout** is usually **10-45 seconds**.

  ✅ **Solution**:
  - Try **increasing** the consumer **session timeout** (`session.timeout.ms`) in your Kafka consumer configuration.

  Example:
  ```python
  from kafka import KafkaConsumer

  consumer = KafkaConsumer(
      'unconfirmed_transactions',
      bootstrap_servers='kafka-broker:9092',
      group_id='my-ingest-app-group',
      session_timeout_ms=60000  # Increase timeout to 60s
  )
  ```

---

### **Key Takeaways**
✅ The logs **don't indicate critical errors**, but they show **frequent consumer churn**, which can affect Kafka performance.  
✅ If this is just from running `kafka-console-consumer.sh` manually, it's expected.  
✅ If `ingest_app` is an actual service, check for **disconnects, crashes, or misconfigurations**.