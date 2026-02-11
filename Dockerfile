FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    unzip \
    build-essential \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install GPAC (MP4Box) from source since gpac package is unavailable in Debian Trixie
RUN wget -q https://github.com/gpac/gpac/archive/refs/tags/v2.4.0.tar.gz \
    && tar -xzf v2.4.0.tar.gz \
    && cd gpac-2.4.0 \
    && ./configure --static-bin \
    && make -j$(nproc) \
    && make install \
    && cd .. \
    && rm -rf gpac-2.4.0 v2.4.0.tar.gz \
    && apt-get remove -y build-essential && apt-get autoremove -y \
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
COPY main.py bot.py config.toml ./

# Note: config.toml is not copied (contains secrets).
# docker run -v $(pwd)/config.toml:/app/config.toml apple-music-bot

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p downloads

CMD ["python", "bot.py"]
