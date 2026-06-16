FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright python-telegram-bot telethon requests
RUN playwright install chromium
RUN playwright install-deps

WORKDIR /app
COPY . .

CMD ["python", "bot_combined.py"]
