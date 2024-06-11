FROM python:3.11-bookworm

LABEL maintainer="Ricardo Filipe dos Santos <ricardofilipecdsantos@gmail.com>"

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
    && poetry install --no-interaction --no-ansi \
    && poetry cache clear --all pypi --no-interaction \
    && rm -rf /root/.cache/pypoetry

RUN playwright install --with-deps webkit

ENTRYPOINT [ "/app/scripts/entrypoint.sh" ]