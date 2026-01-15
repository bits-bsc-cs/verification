# syntax=docker/dockerfile:1

FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends tini && \
    rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

COPY client /app/client
COPY server /app/server
COPY docker/start.sh /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8000 5000 5001

ENTRYPOINT ["/usr/bin/tini", "--", "/app/start.sh"]
