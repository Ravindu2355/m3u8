FROM python:3.10

# Set working directory
WORKDIR /app

# Copy files into container
COPY . .

# Install FFmpeg and Sinhala fonts
RUN apt-get update && apt-get upgrade -y && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ffmpeg \
    fonts-noto \
    fonts-noto-sinhala \
    fonts-lklug-sinhala \
    fontconfig \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-noto-core \
    libreoffice-silgraphite \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD gunicorn --bind 0.0.0.0:8000 app:app & python3 bot.py
