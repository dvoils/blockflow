
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
kubectl apply -f spark-driver-deployment.yaml
kubectl rollout status deployment/ingest-app -n kafka
kubectl get pods -n spark

kubectl apply -f spark-app-deployment.yaml
kubectl delete deployment spark-app -n spark


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

# Delete Pod/Deployment
```bash
kubectl delete pod spark-driver-749fb8cb44-knqm7 -n spark
kubectl delete deployment spark-driver -n spark
```

kubectl create serviceaccount spark -n spark

kubectl rollout restart deployment spark-driver -n spark


docker run -it spark-app:latest ls /opt/spark/bin/spark-submit
docker run -it spark-app:latest bash


kubectl exec -it <POD_NAME> -n spark -- /bin/bash

eval $(minikube docker-env)  # Ensure Minikube is using your local Docker
kubectl rollout restart deployment spark-driver -n spark

docker run -it --name spark-debug bitnami/spark:3.5.4 /bin/bash


kubectl describe pod spark-driver-749fb8cb44-89n8s -n spark



kubectl logs spark-driver-749fb8cb44-89n8s -n spark

kubectl auth can-i patch services --as=system:serviceaccount:spark:spark -n spark

kubectl delete pod -n spark $(kubectl get pods -n spark | grep 'ContainerCannotRun' | awk '{print $1}')

kubectl get configmap -n spark

kubectl describe configmap spark-drv-66fa1c9441fc28ea-conf-map -n spark

kubectl delete configmap spark-drv-e0b3e8944201db0b-conf-map -n spark


/opt/bitnami/spark/bin/spark-submit \
spark-submit \
  --master local \
  --conf spark.jars.ivy=/nonexistent \
  --jars local:///opt/spark/jars/hadoop-aws-3.3.4.jar,local:///opt/spark/jars/aws-java-sdk-bundle-1.11.1026.jar \
  local:///opt/spark/app/spark_app.py
