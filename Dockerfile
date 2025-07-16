FROM python:3.9-alpine

# Install uv
# Note: In some build environments, you may need to add --trusted-host flags for SSL
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org uv

WORKDIR /app
COPY uv.lock pyproject.toml README.md /app/
COPY smsbot /app/smsbot

# Install dependencies
# Note: In some environments, you may need to configure SSL certificates
RUN uv sync --frozen --no-dev

EXPOSE 80/tcp
CMD ["uv", "run", "smsbot"]