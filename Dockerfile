ARG PYTHON_VERSION="3.13"

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


FROM python:${PYTHON_VERSION}-slim-bookworm
COPY --from=builder --chown=app:app /app /app
COPY ./docs/examples/config-basic.ini /app/config.ini
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 5000/tcp
WORKDIR /app
CMD ["smsbot"]
