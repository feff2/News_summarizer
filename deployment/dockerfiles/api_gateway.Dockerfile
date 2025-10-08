# ============================================
# Stage 1: Build Frontend
# ============================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/web_ui

# Копируем package файлы
COPY src/services/web_ui/package*.json ./

# Устанавливаем зависимости
RUN npm install --legacy-peer-deps && \
    npm install --no-save @rollup/rollup-linux-x64-gnu

# Копируем исходный код
COPY src/services/web_ui/ ./

# Собираем production build
RUN npm run build

# Проверяем что сборка прошла успешно
RUN ls -la dist/


# ============================================
# Stage 2: Python Application
# ============================================
FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Устанавливаем Python-зависимости
COPY src/services/api_gateway/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Копируем исходники Python
COPY src/ /app/src/

# Копируем собранный frontend из первого stage
COPY --from=frontend-builder /app/web_ui/dist /app/static

# Проверяем что статика скопировалась
RUN ls -la /app/static/

# Устанавливаем PYTHONPATH
ENV PYTHONPATH=/app/src

# Открываем порты
EXPOSE 8000

# Запускаем FastAPI
CMD ["uvicorn", "src.services.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]