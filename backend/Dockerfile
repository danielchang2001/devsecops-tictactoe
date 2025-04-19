FROM python:3.11-slim
WORKDIR /app
# Upgrade OS packages to patch known vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean
# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy app code
COPY . .
# Run backend on port 8000 inside container
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
