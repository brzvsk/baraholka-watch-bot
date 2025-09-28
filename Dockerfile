FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for state storage
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV STATE_FILE=/app/data/sent_ads.json

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=3 \
  CMD python -c "import sys; sys.path.append('/app/src'); from telegram_bot import TelegramNotifierSync; import os; bot = TelegramNotifierSync(os.getenv('BOT_TOKEN'), os.getenv('CHAT_ID')); exit(0 if bot.test_connection() else 1)" || exit 1

# Run the application
CMD ["python", "main.py"]