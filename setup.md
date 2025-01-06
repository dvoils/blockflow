
# Docker
## Setup Minikube 
```bash
eval $(minikube docker-env)
```
## Build
```bash
docker build -t ingest-app:v1 .
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

# Deploy
```bash
kubectl apply -f ingest-app-deployment.yaml
kubectl apply -f ingest-app-service.yaml
kubectl rollout status deployment/ingest-app -n kafka
```


# Test kafka
```bash
kubectl run kafka-test-producer \
  -n kafka \
  --rm -it \
  --image=wurstmeister/kafka \
  --restart=Never \
  -- /bin/bash
```

## Producer
```bash
/opt/kafka/bin/kafka-console-producer.sh \
  --broker-list kafka-service:9092 \
  --topic unconfirmed_transactions
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

# Delete Pod Deployment
```bash
kubectl delete deployment spark-driver -n spark
```

kubectl create serviceaccount spark -n spark
