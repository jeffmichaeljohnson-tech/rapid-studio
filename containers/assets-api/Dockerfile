FROM python:3.11-slim

WORKDIR /app
COPY . /app

# no need to add user, it already exists in the base image
USER nobody

RUN pip install --no-cache-dir fastapi uvicorn[standard]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


