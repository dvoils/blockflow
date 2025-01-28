FROM spark-with-kafka:3.4.0

# Ensure Spark's bin directory is in PATH
ENV PATH=$PATH:/opt/spark/bin
RUN echo "PATH is $PATH"

# Set the working directory
WORKDIR /opt/app

# Create the upload directory for Spark files
RUN mkdir -p /tmp/spark-upload

# Copy the Spark application
COPY spark_app.py /opt/app/app.py

# Default command for spark-submit
CMD ["spark-submit", \
     "--master", "k8s://https://192.168.49.2:8443", \
     "--deploy-mode", "cluster", \
     "--conf", "spark.kubernetes.namespace=spark", \
     "--conf", "spark.kubernetes.container.image=spark-app:latest", \
     "--conf", "spark.driver.memory=2g", \
     "--conf", "spark.executor.instances=1", \
     "--conf", "spark.executor.memory=2g", \
     "--conf", "spark.executor.cores=1", \
     "--conf", "spark.kubernetes.driver.volumes.persistentVolumeClaim.checkpointpvc.options.claimName=spark-checkpoint-pvc", \
     "--conf", "spark.kubernetes.driver.volumes.persistentVolumeClaim.checkpointpvc.mount.path=/mnt/spark/checkpoints", \
     "--conf", "spark.kubernetes.driver.volumes.persistentVolumeClaim.checkpointpvc.mount.readOnly=false", \
     "--conf", "spark.kubernetes.executor.volumes.persistentVolumeClaim.checkpointpvc.options.claimName=spark-checkpoint-pvc", \
     "--conf", "spark.kubernetes.executor.volumes.persistentVolumeClaim.checkpointpvc.mount.path=/mnt/spark/checkpoints", \
     "--conf", "spark.kubernetes.executor.volumes.persistentVolumeClaim.checkpointpvc.mount.readOnly=false", \
     "--conf", "spark.kubernetes.driver.request.retries=3", \
     "--conf", "spark.kubernetes.file.upload.path=file:///tmp/spark-upload", \
     "--conf", "spark.kubernetes.authenticate.driver.serviceAccountName=spark", \
     "--conf", "spark.kubernetes.authenticate.caCertFile=/etc/ssl/certs/ca-certificates.crt", \
     "--conf", "spark.kubernetes.authenticate.submission.oauthToken=${K8S_TOKEN}", \
     "--conf", "spark.kubernetes.authenticate.caCertFile=/usr/local/share/ca-certificates/minikube-ca.crt", \
     "local:///opt/app/app.py"]
