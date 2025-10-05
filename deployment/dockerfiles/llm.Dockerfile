FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY src/services/llm/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

COPY models/llm/ /app/models/llm
COPY src/services/llm/ /app/src/services/llm/
COPY src/shared/ /app/src/shared/

ENV PYTHONPATH=/app/src:$PYTHONPATH

WORKDIR /app

EXPOSE 8080
CMD ["uvicorn", "services.llm.main:app", "--host", "0.0.0.0", "--port", "8080"]