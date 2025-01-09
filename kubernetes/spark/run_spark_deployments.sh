#!/bin/bash

# Set the namespace
NAMESPACE="spark"

# Check if the namespace exists; if not, create it
if ! kubectl get namespace "$NAMESPACE" > /dev/null 2>&1; then
  echo "Namespace '$NAMESPACE' does not exist. Creating it..."
  kubectl apply -f spark-namespace.yaml
else
  echo "Namespace '$NAMESPACE' already exists."
fi

# List of deployment files to apply
DEPLOYMENT_FILES=(
  "kafka-cluster-role.yaml"
  "kafka-cluster-role-binding.yaml"
  "spark-configmap.yaml"
  "spark-event-logs-pvc.yaml"
  "spark-driver-service.yaml"
  "spark-driver-deployment.yaml"
  "spark-executor-service.yaml"
  "spark-executor-statefulset.yaml"
  "spark-history-server.yaml"
  "spark-role.yaml"
  "spark-role-binding.yaml"
)

# Apply each deployment file
for FILE in "${DEPLOYMENT_FILES[@]}"; do
  if [[ -f "$FILE" ]]; then
    echo "Applying $FILE..."
    kubectl apply -f "$FILE" -n "$NAMESPACE"
  else
    echo "File $FILE not found. Skipping..."
  fi
done

# Wait for the Spark driver pod to be ready
echo "Waiting for Spark driver pod to be ready..."
kubectl wait --for=condition=ready pod -l app=spark-driver -n "$NAMESPACE" --timeout=300s

echo "All deployments applied successfully."
