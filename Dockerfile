# Используем базовый образ Python
FROM python:3.10-slim

WORKDIR /app

# Устанавливаем Tesseract и нужные системные зависимости
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    tesseract-ocr-eng \
    libgl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-зависимости
COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

# Копируем весь проект
COPY . .

# aiogram + логирование
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
