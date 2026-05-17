FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN uv pip install --no-cache -r requirements.txt --system

# Copy backend source code
COPY backend/ .

EXPOSE 8080

# Use shell form to allow environment variable substitution
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"
