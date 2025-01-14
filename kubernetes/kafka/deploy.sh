#!/bin/bash

set -e  # Exit on any error
set -o pipefail  # Catch errors in piped commands

NAMESPACE="kafka"  # Specify your namespace here

# Function to wait for pods to be ready
wait_for_pods() {
    local app_label=$1
    echo "Waiting for pods with label: $app_label to be ready in namespace: $NAMESPACE"
    while true; do
        pods_ready=$(kubectl get pods -n $NAMESPACE -l app=$app_label -o jsonpath='{.items[*].status.containerStatuses[*].ready}' | grep -c false || true)
        total_pods=$(kubectl get pods -n $NAMESPACE -l app=$app_label --no-headers | wc -l || true)
        if [[ $pods_ready -eq 0 && $total_pods -gt 0 ]]; then
            echo "All pods for $app_label are ready."
            break
        fi
        echo "Waiting for $app_label pods to become ready..."
        sleep 5
    done
}

# Ensure the namespace exists
echo "Ensuring namespace '$NAMESPACE' exists..."
kubectl get namespace $NAMESPACE &>/dev/null || kubectl create namespace $NAMESPACE

# Deploy Zookeeper
echo "Deploying Zookeeper..."
kubectl apply -f zookeeper-deployment.yaml -n $NAMESPACE
kubectl apply -f zookeeper-service.yaml -n $NAMESPACE
wait_for_pods "zookeeper"

# Deploy Kafka
echo "Deploying Kafka..."
kubectl apply -f kafka-deployment.yaml -n $NAMESPACE
kubectl apply -f kafka-service.yaml -n $NAMESPACE
wait_for_pods "kafka-broker"  # Adjusted label for Kafka pods

# Deploy Ingest App
echo "Deploying Ingest App..."
kubectl apply -f ingest-app-deployment.yaml -n $NAMESPACE
kubectl apply -f ingest-app-service.yaml -n $NAMESPACE
wait_for_pods "ingest-app"

echo "All services deployed successfully in namespace '$NAMESPACE'!"
