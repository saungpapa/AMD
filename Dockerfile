FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY requirements.txt ./
COPY src/ ./src/
COPY tools/ ./tools/
COPY main.py bot.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create downloads directory
RUN mkdir -p downloads

# Copy config (user should mount their own config)
COPY config.example.toml ./

# Expose no ports (bot connects to Telegram servers)

# Run the bot
CMD ["python", "bot.py"]
