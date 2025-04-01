FROM python:3.12
WORKDIR /app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy dependency files first
COPY Pipfile Pipfile.lock /app/

# Install dependencies
RUN pipenv install --deploy

# Copy the app code
COPY . /app

# Set entrypoint for the Mempool WebSocket Kafka producer
CMD ["pipenv", "run", "python", "/app/mempool_ingest.py"]
