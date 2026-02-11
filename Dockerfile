FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by AMD
# ffmpeg: Audio processing
# gpac (MP4Box): MP4 container manipulation
# bento4 (mp4edit, mp4extract, mp4decrypt): MP4 tools
# unzip: Needed temporarily to extract Bento4
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    gpac \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Bento4 tools
RUN wget -q https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-639.x86_64-unknown-linux.zip \
    && unzip -q Bento4-SDK-1-6-0-639.x86_64-unknown-linux.zip \
    && cp Bento4-SDK-*/bin/* /usr/local/bin/ \
    && rm -rf Bento4-SDK-* *.zip \
    && apt-get remove -y unzip && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml requirements.txt ./
COPY src/ ./src/
COPY tools/ ./tools/
COPY main.py bot.py config.example.toml ./

# Note: config.toml is not copied (contains secrets).
# When running the container, mount your config.toml:
# For Linux/Mac: docker run -v $(pwd)/config.toml:/app/config.toml apple-music-bot
# For Windows PowerShell: docker run -v ${PWD}/config.toml:/app/config.toml apple-music-bot

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create downloads directory
RUN mkdir -p downloads

# Expose no ports (bot connects to Telegram servers)

# Run the bot
CMD ["python", "bot.py"]
