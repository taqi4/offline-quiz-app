FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# System deps for lxml etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persisted SQLite lives here — mount a volume at /app/data in production
VOLUME ["/app/data"]

EXPOSE 5000

# Default: run the web dashboard. Override the command to run the scheduler:
#   docker run ... python main.py schedule
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "webapp.app:app"]
