# syntax=docker/dockerfile:1.7
# Imagen de producción de la API AICC (y, desde O4, del worker: mismo código, otro comando).
# Multi-stage: la etapa final no tiene uv, compiladores ni cachés; corre como usuario sin privilegios.

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.12 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
# Primero solo las dependencias: esta capa se reutiliza mientras uv.lock no cambie.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
ARG APP_VERSION=0.1.0
LABEL org.opencontainers.image.title="aicc-api" \
      org.opencontainers.image.source="https://github.com/MrFtyoQr/AICC" \
      org.opencontainers.image.version="${APP_VERSION}"
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION} \
    PORT=8000
RUN groupadd --system --gid 10001 aicc \
 && useradd --system --uid 10001 --gid aicc --no-create-home --shell /usr/sbin/nologin aicc
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY --chown=aicc:aicc app ./app
COPY --chown=aicc:aicc migrations ./migrations
COPY --chown=aicc:aicc alembic.ini ./
COPY --chown=aicc:aicc --chmod=0755 docker/entrypoint.sh ./entrypoint.sh
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health', timeout=2)"]
ENTRYPOINT ["./entrypoint.sh"]
CMD ["api"]
