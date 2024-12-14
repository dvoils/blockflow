FROM python:3
WORKDIR /app
RUN pip install --no-cache-dir pipenv
COPY . /app
RUN pipenv install --deploy --ignore-pipfile

# Make port 80 available to the world outside this container
EXPOSE 80

ENV NAME World
CMD ["pipenv", "run", "python", "app.py"]
