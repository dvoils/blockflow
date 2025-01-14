
# Docker
## Setup Minikube 
```bash
eval $(minikube docker-env)
```
## Build Docker Images
```bash
docker build -t ingest-app:latest .
docker build -t spark-app:latest .
```

## Using BuildKit
It seems that docker comes installed with the legacy builder for some reason.

DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

```bash
sudo apt install docker-buildx
```

# Update Pipenv
```bash
pipenv shell
pipenv lock
pipenv sync
```

# Deploy Kafka
+ Deploy in this order.
+ Verify the pod is up before deploying the next step

```bash
kubectl apply -f kafka-namespace.yaml

kubectl apply -f zookeeper-deployment.yaml
kubectl apply -f zookeeper-service.yaml

kubectl apply -f kafka-deployment.yaml
kubectl apply -f kafka-service.yaml

kubectl apply -f ingest-app-deployment.yaml
kubectl apply -f ingest-app-service.yaml

kubectl get pods -n kafka
```
# Deploy Spark
```bash
kubectl apply -f spark-namespace.yaml
kubectl apply -f spark-app-job.yaml

kubectl get pods -n spark
```


# Test kafka
## Create test pod
```bash
kubectl run kafka-test-producer \
  -n kafka \
  --rm -it \
  --image=wurstmeister/kafka \
  --restart=Never \
  -- /bin/bash
```

## Consumer
```bash
/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-broker:9092 \
  --topic unconfirmed_transactions \
  --from-beginning
```

## Find Tools
```bash
find / -name kafka-topics.sh 2>/dev/null
```


