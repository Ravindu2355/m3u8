FROM python:3.10

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libass9 \
    libfreetype6 \
    libfribidi0 \
    libharfbuzz0b \
    fontconfig \
    locales \
    && apt-get clean

# Sinhala UTF-8 locale
RUN sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Copy Sinhala fonts
RUN mkdir -p /usr/share/fonts/truetype/sinhala
COPY fonts/ /usr/share/fonts/truetype/sinhala/

RUN fc-cache -fv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#CMD python3 bot.py
CMD gunicorn --bind 0.0.0.0:8000 app:app & python3 bot.py
