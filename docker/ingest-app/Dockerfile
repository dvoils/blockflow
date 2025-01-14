FROM python:3.12
WORKDIR /app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy only the necessary files
COPY Pipfile Pipfile.lock /app/

# Install dependencies based on the Pipfile.lock
RUN pipenv install --deploy

# Copy the rest of the application
COPY . /app

CMD ["pipenv", "run", "python", "/app/ingest_app.py"]