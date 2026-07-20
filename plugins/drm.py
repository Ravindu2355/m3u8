FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

WORKDIR /app

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

RUN sed -i \
    's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' \
    /etc/locale.gen \
    && locale-gen en_US.UTF-8

RUN mkdir -p /usr/share/fonts/truetype/sinhala

COPY fonts/ /usr/share/fonts/truetype/sinhala/

RUN fc-cache -fv

RUN python -m pip install --no-cache-dir \
    --upgrade \
    pip \
    setuptools \
    wheel

RUN pip install --no-cache-dir \
    "setuptools<81"

RUN python -m pip install --no-cache-dir yt-dlp


# ─────────────────────────────────────
# Install Shaka Packager
# ─────────────────────────────────────

ENV SHAKA_PACKAGER_URL="https://github.com/shaka-project/shaka-packager/releases/download/v3.9.2/packager-linux-x64"

RUN wget -O /usr/local/bin/packager "$SHAKA_PACKAGER_URL" \
    && chmod +x /usr/local/bin/packager


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


RUN mkdir -p /app/downloads


# ─────────────────────────────────────
# Verify installations
# ─────────────────────────────────────

RUN echo "===== FFmpeg =====" \
    && ffmpeg -version | head -n 1 \
    && echo "===== yt-dlp =====" \
    && yt-dlp --version \
    && echo "===== Shaka Packager =====" \
    && which packager \
    && packager --version


CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8000 app:app & exec python3 bot.py"]
