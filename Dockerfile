FROM python:3.9-alpine AS base

# Builder
FROM base AS builder

# Install uv
RUN pip install uv

WORKDIR /src
COPY uv.lock pyproject.toml README.md /src/
COPY smsbot /src/smsbot

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev

# Final container
FROM base AS runtime

COPY --from=builder /src/.venv /runtime
ENV PATH=/runtime/bin:$PATH
EXPOSE 80/tcp
CMD ["smsbot"]