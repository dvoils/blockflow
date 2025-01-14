FROM apache/spark-py:v3.4.0

# Set the working directory
WORKDIR /opt/app

# Add Spark to PATH
ENV PATH=$PATH:/opt/spark/bin

# Copy application files into the image
COPY spark_app.py /opt/app/app.py

# Set the default command
CMD ["spark-submit", "/opt/app/app.py"]
