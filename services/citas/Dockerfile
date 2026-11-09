FROM python:3.12-slim

ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --system --uid 10001 citas
USER citas

EXPOSE 8080

CMD ["python", "-m", "app"]
