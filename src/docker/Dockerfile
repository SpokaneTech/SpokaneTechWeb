FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
COPY src/django_project /app/

RUN chmod +x /app/entrypoint.sh
RUN pip install --upgrade pip pip-tools
RUN pip install .[docker]
RUN playwright install --with-deps

# Expose the port that the app runs on
EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
