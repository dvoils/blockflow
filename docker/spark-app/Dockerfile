FROM apache/spark-py:v3.4.0

WORKDIR /opt/app

ENV PATH=$PATH:/opt/spark/bin

COPY spark_app.py /opt/app/app.py

CMD ["spark-submit", "/opt/app/app.py"]
