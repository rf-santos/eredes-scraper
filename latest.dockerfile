FROM docker.io/library/python:3.11

LABEL maintainer="Ricardo Filipe dos Santos <ricardofilipecdsantos@gmail.com>"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o /tmp/chrome.deb \
    && dpkg -i /tmp/chrome.deb || apt-get install -yf \
    && rm -rf /tmp/chrome.deb \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir \
    eredesscraper \
    && pip cache purge

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

CMD ["ers"]