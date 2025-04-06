FROM python:3.10

# Set working directory
WORKDIR /app

# Copy files into container
COPY . .

# Install FFmpeg and Sinhala fonts
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-noto \
    fonts-lklug-sinhala \
    fontconfig \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-noto-core \
    && apt-get clean

# Copy Iskoola Pota font into fonts directory
RUN mkdir -p /usr/share/fonts/truetype/iskoola
COPY iskpota.ttf /usr/share/fonts/truetype/iskoola/

# Rebuild font cache
RUN fc-cache -f -v

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD gunicorn --bind 0.0.0.0:8000 app:app & python3 bot.py
