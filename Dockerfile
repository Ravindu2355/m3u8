FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install FFmpeg and Sinhala fonts
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    ttf-mscorefonts-installer \
    fontconfig \
    && apt-get clean

# Verify font installation
RUN fc-list | grep Sinhala || echo "No Sinhala fonts found"

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Run the bot when the container launches
CMD gunicorn --bind 0.0.0.0:8000 app:app & python3 bot.py
