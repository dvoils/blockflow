# BlockFlow

**BlockFlow** is a cloud-agnostic, open-source project designed to process, store, and visualize real-time blockchain transaction data. Leveraging Apache Kafka, Apache Spark, TimescaleDB, and Grafana, it demonstrates modern data engineering practices in a cost-effective and portable manner.

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

## License

Licensed under the MIT License. See [LICENSE](LICENSE).

For more information, visit [GitHub](https://github.com/your-username/blockflow).

