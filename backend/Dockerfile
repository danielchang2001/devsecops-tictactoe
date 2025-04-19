# Build Stage
FROM python:3.11-slim-bookworm as builder

WORKDIR /app

# Install build dependencies and upgrade OS packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y build-essential && apt-get clean

COPY requirements.txt .

# Install packages in a virtualenv to copy later
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final Runtime Stage
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy only installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
