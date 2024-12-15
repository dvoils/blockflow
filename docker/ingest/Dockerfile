FROM python:3.12
WORKDIR /app

ENV PIPENV_VERBOSITY=-1
RUN pip install --no-cache-dir --root-user-action=ignore pipenv 

ENV VIRTUAL_ENV=/app/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY . /app
RUN pipenv install --deploy --ignore-pipfile
