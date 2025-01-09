# Use the Bitnami Spark base image
FROM bitnami/spark:3.5.4

# Install curl for downloading files
USER root
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/spark/app

# Download and set up Ivy
RUN curl -o /opt/ivy.jar https://repo1.maven.org/maven2/org/apache/ivy/ivy/2.5.1/ivy-2.5.1.jar && \
    echo -e '#!/bin/bash\njava -jar /opt/ivy.jar "$@"' > /usr/local/bin/ivy && \
    chmod +x /usr/local/bin/ivy

# Verify Ivy installation
RUN ivy -version

# Copy your application files
COPY . /opt/spark/app/

# Preload Spark dependencies into the JAR directory
RUN mkdir -p /opt/spark/jars && \
    curl -o /opt/spark/jars/hadoop-aws-3.3.4.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -o /opt/spark/jars/aws-java-sdk-bundle-1.11.1026.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.1026/aws-java-sdk-bundle-1.11.1026.jar

# Set SPARK_HOME environment variable
ENV SPARK_HOME=/opt/bitnami/spark

# Expose Spark UI port
EXPOSE 4040

# Command to run your Spark application
CMD ["/opt/bitnami/spark/bin/spark-submit", \
     "--master", "local", \
     "--jars", "local:///opt/spark/jars/hadoop-aws-3.3.4.jar,local:///opt/spark/jars/aws-java-sdk-bundle-1.11.1026.jar", \
     "local:///opt/spark/app/spark_app.py"]
