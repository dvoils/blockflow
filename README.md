# BlockFlow

**BlockFlow** is an ongoing project leveraging Kubernetes to process, store, and visualize real-time blockchain transaction data. Using tools like Apache Kafka, Apache Spark, TimescaleDB, and Grafana, it emphasizes scalability, efficiency, and portability for real-time blockchain transaction analysis.

## Key Features

- **Real-Time Ingestion:** WebSocket API -> Apache Kafka.
- **Scalable ETL:** Apache Spark Structured Streaming.
- **Time-Series Storage:** TimescaleDB (PostgreSQL extension).
- **Visualization:** Grafana dashboards.
- **Centralized Logging:** Fluent Bit -> Loki -> Grafana.
- **Cloud-Agnostic:** Kubernetes orchestrated.

## Architecture

- **Ingestion:** WebSocket -> Kafka.
- **Processing:** Spark Structured Streaming.
- **Storage:** TimescaleDB for efficient time-series querying.
- **Visualization:** Grafana for real-time dashboards.
- **Logging:** Fluent Bit and Loki stack.

Licensed under the MIT License. See [LICENSE](LICENSE).
