FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV VENV=/opt/venv
RUN python -m venv $VENV
ENV PATH="$VENV/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

COPY src/services/db/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY src/ /app/src/

ENV PYTHONPATH=/app
WORKDIR /app

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "src.services.db.main:app", "--host", "0.0.0.0", "--port", "8001"]