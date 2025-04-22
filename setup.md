
# Minikube
## Start Minikube
```bash
minikube config set memory 6144
minikube config set cpus 4
minikube delete
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
+ Put the certification into `docker/base-spark-kafka`

## Determine Minikube's IP
minikube ip

# Install kubectl
You need to install `kubectl` using the `--classic` flag because it requires classic confinement to function properly. Run the following command:

```sh
sudo snap install kubectl --classic
```

- Ubuntu’s `snap` packages are usually confined to a sandbox for security.
- `kubectl` needs broader system access to interact with Kubernetes clusters, so it uses - The warning is just an informational message—`kubectl` is safe to install this way.

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
docker build -t confirmed-blocks-ingest:latest .
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

kubectl apply -f confirmed-blocks-ingest-deployment.yaml

kubectl get pods -n kafka
```

# Deploy Spark
## Create Spark namespace
```bash
kubectl apply -f spark-namespace.yaml
```

## Create Service Account
```bash
kubectl create serviceaccount spark -n spark
# kubectl apply -f serviceaccount.yaml
```

## Bind the ServiceAccount to a Role
```bash
kubectl apply -f role.yaml
kubectl apply -f rolebinding.yaml
kubectl -n spark --as="system:serviceaccount:spark:spark" auth can-i deletecollection configmaps
+ should return - yes
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

## Create Kubernetes IP Config Map
```bash
kubectl create configmap spark-config \
  --from-literal=SPARK_K8S_API_SERVER=$(minikube ip) \
  --from-file=/home/dvoils/Desktop/blockflow/docker/base-spark-kafka/spark-defaults.conf \
  --from-file=/home/dvoils/Desktop/blockflow/docker/base-spark-kafka/log4j.properties \
  -n spark
```

## Check Service Account and Roles
```bash
kubectl get serviceaccounts -n spark
kubectl get roles -n spark
kubectl get clusterroles
kubectl get clusterrolebindings
```

## Create Persistent Volumes for Spark in Minkkube
```bash
minikube ssh
sudo mkdir -p /mnt/spark/checkpoints
sudo chmod -R 777 /mnt/spark/checkpoints
sudo mkdir -p /mnt/spark/logs
sudo chmod -R 777 /mnt/spark/logs
```

## Create Persistent Volume
```bash
kubectl apply -f spark-checkpoint-volume.yaml
kubectl apply -f spark-checkpoint-claim.yaml
kubectl apply -f spark-logs-volume.yaml
kubectl apply -f spark-logs-claim.yaml
```
## Create Fluent Bit Configmap
```bash
kubectl apply -f fluentbit-config.yaml -n spark
kubectl apply -f spark-rbac.yaml -n spark
```

## Create Job or Deployment
```bash
kubectl apply -f spark-app-job.yaml
kubectl apply -f spark-app-deployment.yaml
kubectl apply -f spark-app-service.yaml

kubectl get pods -n spark
```


# Test kafka
+ These tests are set up to consume only new messages.

## Create Test Pod
```bash
   kubectl run kafka-debugger -n kafka --image=wurstmeister/kafka --restart=Never -- sleep infinity
```

## Exec into Test Pod
```bash
   kubectl exec -it kafka-debugger -n kafka -- /bin/bash
```

## Ingestion Steam
```bash
   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-broker:9092 --topic unconfirmed_transactions --group kafka-debug-group
```

## Confirmed Blocks Ingestion Stream
```bash
   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-broker:9092 --topic confirmed_blocks --group kafka-debug-group
```

## Spark Logs Stream
```bash
   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-broker:9092 --topic spark-logs --group kafka-debug-group
```

## Spark Transactions Data Stream 
```bash
   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-broker:9092 --topic processed_transactions --group kafka-debug-group
```

## Spark Confirmed Blocks Data Stream 
```bash
   /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-broker:9092 --topic processed_confirmed_blocks --group kafka-debug-group
```






## Find Tools
```bash
find / -name kafka-topics.sh 2>/dev/null
```


