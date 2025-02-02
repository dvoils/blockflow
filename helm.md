# Helm Chart: blockflow
# File: Chart.yaml
apiVersion: v2
name: blockflow
version: 0.1.0
description: Helm chart for deploying Kafka-Spark with Istio on Minikube and Cloud

---
# File: values.yaml (Default values for both environments)
namespace: blockflow
replicaCount: 1

kafka:
  image: wurstmeister/kafka
  brokerId: "1"
  listeners: "PLAINTEXT://0.0.0.0:9092"
  advertisedListeners: "PLAINTEXT://kafka-broker.kafka.svc.cluster.local:9092"
  storage:
    size: 1Gi

spark:
  image: spark-app:latest
  executorMemory: "2g"
  executorInstances: 1
  checkpointPVC: "spark-checkpoint-pvc"

istio:
  enabled: true

---
# File: values-minikube.yaml (Overrides for Minikube)
kafka:
  storage:
    size: 500Mi

spark:
  executorMemory: "1g"
  executorInstances: 1

---
# File: values-cloud.yaml (Overrides for Cloud)
kafka:
  storage:
    size: 10Gi

spark:
  executorMemory: "4g"
  executorInstances: 3

---
# File: templates/kafka-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka-broker
  namespace: {{ .Values.namespace }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: kafka-broker
  template:
    metadata:
      labels:
        app: kafka-broker
    spec:
      containers:
      - name: kafka-broker
        image: {{ .Values.kafka.image }}
        env:
        - name: KAFKA_BROKER_ID
          value: "{{ .Values.kafka.brokerId }}"
        - name: KAFKA_LISTENERS
          value: "{{ .Values.kafka.listeners }}"
        - name: KAFKA_ADVERTISED_LISTENERS
          value: "{{ .Values.kafka.advertisedListeners }}"
        ports:
        - containerPort: 9092

---
# File: templates/spark-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spark-streaming-app
  namespace: {{ .Values.namespace }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: spark-streaming-app
  template:
    metadata:
      labels:
        app: spark-streaming-app
    spec:
      containers:
      - name: spark-streaming-app
        image: {{ .Values.spark.image }}
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka-broker.{{ .Values.namespace }}.svc.cluster.local:9092"
        ports:
        - containerPort: 4040

---
# File: templates/istio-mtls.yaml (Optional if Istio is enabled)
{{- if .Values.istio.enabled }}
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: kafka-mtls
  namespace: {{ .Values.namespace }}
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: spark-mtls
  namespace: {{ .Values.namespace }}
spec:
  mtls:
    mode: STRICT
{{- end }}

---
# Helm Deployment Commands:
# Install on Minikube:
helm install blockflow ./helm/blockflow -f values-minikube.yaml

# Install on Cloud:
helm install blockflow ./helm/blockflow -f values-cloud.yaml
