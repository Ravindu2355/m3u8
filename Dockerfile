FROM python:3.10

# Set working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install FFmpeg and necessary fonts for Sinhala subtitles
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-noto-core \
    fontconfig \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD gunicorn --bind 0.0.0.0:8000 app:app & python3 bot.py
