FROM python:3.12

# Set the working directory
WORKDIR /app

# Install pipenv
ENV PIPENV_VERBOSITY=-1
RUN pip install --no-cache-dir --root-user-action=ignore pipenv 


# Create and activate a virtual environment
ENV VIRTUAL_ENV=/app/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy project files into the container
COPY . /app

# Install dependencies using pipenv in the virtual environment
RUN pipenv install --deploy --ignore-pipfile
