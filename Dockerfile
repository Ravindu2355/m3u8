FROM python:3.10-slim

# ─────────────────────────────────────
# Environment
# ─────────────────────────────────────

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

WORKDIR /app


# ─────────────────────────────────────
# System packages
# ─────────────────────────────────────

RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    unzip \
    ca-certificates \
    libass9 \
    libfreetype6 \
    libfribidi0 \
    libharfbuzz0b \
    fontconfig \
    locales \
    && rm -rf /var/lib/apt/lists/*


# ─────────────────────────────────────
# UTF-8 locale
# ─────────────────────────────────────

RUN sed -i \
    's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' \
    /etc/locale.gen \
    && locale-gen en_US.UTF-8


# ─────────────────────────────────────
# Sinhala fonts
# ─────────────────────────────────────

RUN mkdir -p /usr/share/fonts/truetype/sinhala

COPY fonts/ /usr/share/fonts/truetype/sinhala/

RUN fc-cache -fv


# ─────────────────────────────────────
# Install yt-dlp
# ─────────────────────────────────────

RUN python -m pip install --no-cache-dir \
    --upgrade \
    pip \
    setuptools \
    wheel

RUN python -m pip install --no-cache-dir yt-dlp


# ─────────────────────────────────────
# Download Bento4 automatically
# ─────────────────────────────────────

ENV BENTO4_URL="https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip"

RUN mkdir -p /tmp/bento4 \
    && wget -O /tmp/bento4/bento4.zip "$BENTO4_URL" \
    && unzip -q /tmp/bento4/bento4.zip -d /tmp/bento4 \
    && find /tmp/bento4 -type f -name mp4decrypt -exec cp {} /usr/local/bin/mp4decrypt \; \
    && chmod +x /usr/local/bin/mp4decrypt \
    && rm -rf /tmp/bento4


# ─────────────────────────────────────
# Python requirements
# ─────────────────────────────────────

COPY requirements.txt .

RUN pip install --no-cache-dir \
    -r requirements.txt


# ─────────────────────────────────────
# Copy project
# ─────────────────────────────────────

COPY . .


# ─────────────────────────────────────
# Create folders
# ─────────────────────────────────────

RUN mkdir -p /app/downloads


# ─────────────────────────────────────
# Verify installations
# ─────────────────────────────────────

RUN echo "===== FFmpeg =====" \
    && ffmpeg -version | head -n 1 \
    && echo "===== yt-dlp =====" \
    && yt-dlp --version \
    && echo "===== mp4decrypt =====" \
    && which mp4decrypt \
    && mp4decrypt || true


# ─────────────────────────────────────
# Start Flask + Bot
# ─────────────────────────────────────

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8000 app:app & exec python3 bot.py"]
