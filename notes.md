
kubectl exec -it spark-streaming-app-xxxxxx -c spark-streaming-app -n spark -- tail -f /mnt/spark/logs/spark-app.log
kubectl exec -it spark-streaming-app-7d8f6d56d8-jgj8x -c spark-streaming-app -n spark -- tail -f /mnt/spark/logs/spark-app.log


kubectl delete pod -n spark -l app=spark-streaming-app

kubectl logs spark-streaming-app-7bb695b759-hv6qn -n spark
kubectl describe pod spark-streaming-app-7bb695b759-hv6qn -n spark

kubectl logs -f spark-streaming-app-7d8f6d56d8-kk8bv -c fluent-bit -n spark
kubectl exec -it spark-streaming-app-7bb695b759-hv6qn -n spark -- bash
kubectl describe pod spark-streaming-app-7d8f6d56d8-tr8zk -n spark




kubectl describe node minikube


docker run -it --user root spark-with-kafka:3.4.0 bash
docker run -it --user root spark-app:latest bash


minikube delete

kubectl delete deployment spark-streaming-app -n spark

kubectl delete deployment spark-app -n spark
kubectl delete pods --all -n spark


kubectl get pod spark-app-8d9974b9d-mqsmx -n spark -o yaml

kubectl exec -it spark-app-8d9974b9d-mqsmx -n spark -- bash

spark-submit \
    --master k8s://https://192.168.49.2:8443 \
    --deploy-mode cluster \
    --conf spark.kubernetes.namespace=spark \
    --conf spark.kubernetes.container.image=spark-with-kafka:3.4.0 \
    --conf spark.executor.instances=2 \
    --conf spark.executor.memory=1g \
    --conf spark.executor.cores=1 \
    --conf spark.kubernetes.file.upload.path=file:///tmp/spark-upload \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.authenticate.caCertFile=/etc/ssl/certs/ca-certificates.crt \
    --conf spark.kubernetes.authenticate.submission.oauthToken=${K8S_TOKEN} \
    --conf spark.kubernetes.authenticate.caCertFile=/usr/local/share/ca-certificates/minikube-ca.crt \
    /opt/app/app.py




kubectl exec -it spark-app-8d9974b9d-hf2jq -n spark -- bash



Inside the container, the output confirms that your Minikube CA certificate has been successfully added to the JVM trust store

keytool -list -keystore /opt/java/openjdk/lib/security/cacerts -storepass changeit | grep -i minikube
Warning: use -cacerts option to access cacerts keystore
minikube-ca, Jan 20, 2025, trustedCertEntry, 




kubectl get serviceaccounts -n spark
kubectl get roles -n spark
kubectl get clusterroles
kubectl get clusterrolebindings



kubectl delete job spark-app-job -n spark


kubectl auth can-i create pods --as=system:serviceaccount:spark:spark -n spark
kubectl auth can-i get pods --as=system:serviceaccount:spark:spark -n spark
kubectl auth can-i get configmaps --as=system:serviceaccount:spark:spark -n spark



docker cp ~/.minikube/ca.crt 30afeebabdf6:/usr/local/share/ca-certificates/minikube-ca.crt
docker cp ~/.minikube/ca.key 30afeebabdf6:/usr/local/share/ca-certificates/minikube-ca.key
docker cp ~/.minikube/ca.pem 30afeebabdf6:/usr/local/share/ca-certificates/minikube-ca.pem

curl -k https://192.168.49.2:8443 \
     --header "Authorization: Bearer $K8S_TOKEN" \
     --cacert /usr/local/share/ca-certificates/minikube-ca.crt



curl -k https://192.168.49.2:8443 \
     --header "Authorization: Bearer $K8S_TOKEN" \
     --cacert /usr/local/share/ca-certificates/minikube-ca.crt

docker run -it spark-app:latest bash

K8S_TOKEN=$(kubectl get secret spark-token -n spark -o jsonpath='{.data.token}' | base64 --decode)

docker run -it --rm \
  -e K8S_TOKEN="${K8S_TOKEN}" \
  spark-app:latest bash


export K8S_TOKEN=$(kubectl get secret spark-token -n spark -o jsonpath='{.data.token}' | base64 --decode)



spark-submit \
    --master k8s://https://192.168.49.2:8443 \
    --deploy-mode cluster \
    --conf spark.kubernetes.namespace=spark \
    --conf spark.kubernetes.container.image=spark-with-kafka:3.4.0 \
    --conf spark.executor.instances=3 \
    --conf spark.executor.memory=2g \
    --conf spark.executor.cores=1 \
    --conf spark.kubernetes.file.upload.path=file:///tmp/spark-upload \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.authenticate.caCertFile=/etc/ssl/certs/ca-certificates.crt \
    --conf spark.kubernetes.authenticate.submission.oauthToken=${K8S_TOKEN} \
    --conf spark.kubernetes.authenticate.caCertFile=/usr/local/share/ca-certificates/minikube-ca.crt \
    /opt/app/app.py



1. Create service account and roles
kubectl create serviceaccount spark -n spark (maybe this is already done)
create role.yaml and apply
create rolebinding.yaml and apply

2. Manually Create a Service Account Token Secret
create spark-token.yaml and apply


docker build --no-cache -t spark-with-kafka:3.4.0 -f Dockerfile.base .
docker build --no-cache -t spark-app:latest .

openssl crl2pkcs7 -nocrl -certfile /etc/ssl/certs/ca-certificates.crt | openssl pkcs7 -print_certs -noout | grep kube






cat docker/ingest-app/Dockerfile
cat docker/ingest-app/ingest_app.py
cat docker/spark-app/Dockerfile
cat docker/spark-app/spark_app.py

cat kubernetes/kafka/*.yaml
cat kubernetes/spark-app/*.yaml

docker run -it --rm spark-app:latest bash
docker run -it --rm spark-with-kafka:3.4.0 bash

spark-submit /opt/app/app.py

docker rmi d188efcaf113
Error response from daemon: conflict: unable to delete d188efcaf113 (must be forced) - image is being used by stopped container 6e95f227fefc

docker ps -a

docker stop 6e95f227fefc


kubectl delete deployment spark-app -n spark

docker rmi d188efcaf113


# Delete Pod/Deployment
```bash
kubectl delete pod spark-driver-749fb8cb44-knqm7 -n spark
kubectl delete deployment spark-driver -n spark
kubectl delete job spark-app-job -n spark

```


kubectl rollout status deployment/ingest-app -n kafka

kubectl create serviceaccount spark -n spark

kubectl rollout restart deployment spark-driver -n spark


docker run -it spark-app:latest ls /opt/spark/bin/spark-submit
docker run -it spark-app:latest bash


kubectl exec -it <POD_NAME> -n spark -- /bin/bash

eval $(minikube docker-env)  # Ensure Minikube is using your local Docker
kubectl rollout restart deployment spark-driver -n spark

docker run -it --name spark-debug bitnami/spark:3.5.4 /bin/bash


kubectl describe pod spark-driver-749fb8cb44-89n8s -n spark


kubectl logs ingest-app-57cb7677f-qzc75 -n kafka --previous

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


spark-submit \
  --master local \
  local:///opt/spark/app/spark_app.py