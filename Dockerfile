# Используем базовый образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости + tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    tesseract-ocr-eng \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем Python-библиотеки
COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

# Копируем весь проект
COPY . .

# Устанавливаем переменную окружения для aiogram
ENV PYTHONUNBUFFERED=1

# Запускаем бота
CMD ["python", "bot.py"]
