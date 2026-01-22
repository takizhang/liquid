FROM python:3.11-slim

WORKDIR /app

# Copy backend code
COPY backend/ /app/backend/
COPY config/ /app/config/
COPY .env.example /app/.env

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Expose port
EXPOSE 7860

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=7860

# Start command
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
