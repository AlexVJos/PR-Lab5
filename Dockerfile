FROM python:3.13-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY . .

ENV DJANGO_SETTINGS_MODULE=app.settings

CMD ["/bin/sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 app.asgi:application"]
