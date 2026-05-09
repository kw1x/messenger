# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.4.30-python3.13-bookworm-slim AS builder

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY libs/hexachat-shared/pyproject.toml libs/hexachat-shared/pyproject.toml
COPY services/chat-core/pyproject.toml services/chat-core/pyproject.toml
COPY services/presence-gateway/pyproject.toml services/presence-gateway/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --package presence-gateway

COPY libs/hexachat-shared libs/hexachat-shared
COPY services/presence-gateway services/presence-gateway

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package presence-gateway

FROM python:3.13-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /workspace/services/presence-gateway /app
COPY --from=builder /workspace/libs/hexachat-shared /workspace/libs/hexachat-shared

WORKDIR /app
USER app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--proxy-headers", "--ws", "websockets"]
