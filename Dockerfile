FROM python:3.11-alpine
WORKDIR /app
COPY . /app
RUN pip install .
ENTRYPOINT smsbot