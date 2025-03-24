FROM spark-with-kafka:3.4.0

# Ensure Spark's bin directory is in PATH
ENV PATH=$PATH:/opt/spark/bin
RUN echo "PATH is $PATH"

# Set the working directory
WORKDIR /opt/app

# Create upload directory for Spark file uploads
RUN mkdir -p /tmp/spark-upload

# Copy Spark application and defaults file
COPY spark_app.py /opt/app/app.py
# COPY spark-defaults.conf /opt/spark/conf/spark-defaults.conf

# Default command
CMD ["spark-submit", "local:///opt/app/app.py"]
