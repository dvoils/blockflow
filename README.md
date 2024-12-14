# BlockFlow

<<<<<<< HEAD
**BlockFlow** is a data pipeline built on Kubernetes to process, store, and visualize real-time blockchain transaction data. Using tools like Apache Kafka, Apache Spark, TimescaleDB, and Grafana, it focuses on scalability, efficiency, and portability, enabling blockchain transaction analysis.
=======
**BlockFlow** is a cloud-agnostic project designed to process, store, and visualize real-time blockchain transaction data. Leveraging Apache Kafka, Apache Spark, TimescaleDB, and Grafana, it demonstrates modern data engineering practices in a cost-effective and portable manner.
>>>>>>> 47bce2bda8a3993690007a25eee8dcc2c155c2d9

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
<<<<<<< HEAD
=======

For more information, visit [GitHub](https://github.com/your-username/blockflow).
>>>>>>> 47bce2bda8a3993690007a25eee8dcc2c155c2d9
