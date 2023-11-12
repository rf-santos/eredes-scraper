FROM docker.io/library/python:3.11

LABEL maintainer="Ricardo Filipe dos Santos <ricardofilipecdsantos@gmail.com>"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4

RUN curl -fSsL https://dl.google.com/linux/linux_signing_key.pub | \
    gpg --dearmor | \
    tee /usr/share/keyrings/google-chrome.gpg >> /dev/null

RUN echo deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main | \
    tee /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir \
    poetry==1.6.1 \
    && pip cache purge

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_CREATE=false

RUN mkdir -p /app

COPY . /app

WORKDIR /app

RUN poetry config virtualenvs.create false \
    && poetry install --with dev --no-interaction --no-ansi \
    && poetry cache clear --all pypi --no-interaction \
    && rm -rf /root/.cache/pypoetry

# CMD ["ers"]