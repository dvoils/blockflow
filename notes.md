
docker run -it --rm spark-app:latest /bin/bash
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