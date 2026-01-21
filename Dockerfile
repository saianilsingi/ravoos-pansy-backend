FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# project files
COPY . .

# collect static later in prod
EXPOSE 8000

CMD ["gunicorn", "ravoos_pansy.wsgi:application", "--bind", "0.0.0.0:8000"]
