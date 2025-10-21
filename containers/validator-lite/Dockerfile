FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir redis requests

USER 65534
CMD ["python", "validator.py"]
