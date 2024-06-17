FROM python:3.12

WORKDIR /app

COPY requirements.lock requirements-dev.lock pyproject.toml .env /app/
COPY ./src /app/src

RUN pip install uv
RUN uv pip install --system -r requirements-dev.lock
