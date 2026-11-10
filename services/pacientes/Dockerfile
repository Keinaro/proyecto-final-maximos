FROM python:3.12-slim

ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db.py schemas.py main.py ./

# Usuario sin privilegios
RUN useradd --system --no-create-home app
USER app

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]