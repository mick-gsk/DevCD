# syntax=docker/dockerfile:1
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEVCD_HOST=0.0.0.0 \
    DEVCD_PORT=8765 \
    DEVCD_RUNTIME_DIR=/data

WORKDIR /app

COPY pyproject.toml README.md LICENSE SECURITY.md ./
COPY packages/devcd-core/src ./packages/devcd-core/src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir . \
    && useradd --create-home --home-dir /home/devcd --shell /usr/sbin/nologin devcd \
    && mkdir -p /data \
    && chown -R devcd:devcd /data /home/devcd

USER devcd
VOLUME ["/data"]
EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["python", "-c", "from pathlib import Path; import urllib.request; token=Path('/data/token').read_text(encoding='utf-8').strip(); request=urllib.request.Request('http://127.0.0.1:8765/state', headers={'Authorization': f'Bearer {token}'}); urllib.request.urlopen(request, timeout=2).read()"]

CMD ["devcd", "run", "--host", "0.0.0.0", "--port", "8765"]
