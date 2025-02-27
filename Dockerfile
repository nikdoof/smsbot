FROM python:3.9-alpine AS base

# Builder
FROM base AS builder

ENV POETRY_VERSION=2.1.1

RUN apk add build-base unzip wget python3-dev libffi-dev rust cargo openssl-dev && pip install "poetry==$POETRY_VERSION" && poetry self add poetry-plugin-bundle
WORKDIR /src
COPY poetry.lock pyproject.toml README.md /src/
COPY smsbot /src/smsbot
RUN poetry bundle venv /runtime


# Final container
FROM base AS runtime

COPY --from=builder /runtime /runtime
ENV PATH=/runtime/bin:$PATH
EXPOSE 8000/tcp
CMD ["smsbot"]