FROM python:3.12
WORKDIR /opt/spark/app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock to install dependencies
COPY Pipfile Pipfile.lock /opt/spark/app/

# Install dependencies using pipenv
RUN pipenv install --deploy

# Copy the rest of the application
COPY . /opt/spark/app/

# Expose Spark UI port
EXPOSE 4040

# Set the entrypoint to run your Spark application via pipenv
CMD ["pipenv", "run", "spark-submit", "--master", "local[*]", "--deploy-mode", "client", "/opt/spark/app/spark_app.py"]
