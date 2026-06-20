# Multi-stage build (DEO 8.9)
FROM python:3.11-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.11-slim AS runtime

ARG GIT_COMMIT=unknown
ENV BGA_GIT_COMMIT=$GIT_COMMIT
ENV BELESKE_GIT_COMMIT=$GIT_COMMIT

WORKDIR /app
RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /app/.venv /app/.venv
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini config ./

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD ["bga", "health"]

CMD ["/bin/bash"]
