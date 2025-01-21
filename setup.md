
# Minikube
## Start Minikube
```bash
minikube config set memory 6144
minikube config set cpus 4
minikube start
minikube config view
```

## Use Minikube's Docker Repository
```bash
eval $(minikube docker-env)
docker info | grep "Name:"
```

## Export Minikube's CA Certificate
+ Get the certification, in this case using minikube's
```bash
minikube ssh cat /var/lib/minikube/certs/ca.crt > minikube-ca.crt
```
+ Put the certification into `docker/base-spark-app`

# Docker
## Using BuildKit
It seems that docker comes installed with the legacy builder for some reason.

DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

```bash
sudo apt install docker-buildx
```

## Build Docker Images
```bash
docker build -t spark-with-kafka:3.4.0 -f Dockerfile.base .
docker build -t ingest-app:latest .
docker build -t spark-app:latest .
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
## Create Spark namespace
```bash
kubectl apply -f spark-namespace.yaml
```

## Create Service Account
```bash
#kubectl create serviceaccount spark -n spark
kubectl apply -f serviceaccount.yaml
```

## Bind the ServiceAccount to a Role
```bash
kubectl apply -f role.yaml
kubectl apply -f rolebinding.yaml
```
## Create a Token Secret
```bash
kubectl apply -f spark-token.yaml
kubectl get secrets -n spark
kubectl describe secret spark-token -n spark
```

## Create Spark Token Secret
```bash
K8S_TOKEN=$(kubectl get secret spark-token -n spark -o jsonpath='{.data.token}' | base64 --decode)
kubectl create secret generic spark-token-secret \
    -n spark \
    --from-literal=token="${K8S_TOKEN}"
kubectl describe secret spark-token-secret -n spark
```
## Create Job or Deployment
```bash
kubectl apply -f spark-app-job.yaml
kubectl apply -f spark-app-deployment.yaml
kubectl apply -f spark-app-service.yaml

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


