# ====================
# Stage 1: Builder
# ====================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies needed for building and running Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libx11-xcb1 libxcomposite1 libxrandr2 \
    libxdamage1 libgbm1 libasound2 libpangocairo-1.0-0 \
    libatk-bridge2.0-0 libgtk-3-0 fonts-liberation libxshmfence1 \
    libxcb1 xdg-utils netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv (fast dependency resolver) and create virtualenv
RUN pip install --no-cache-dir uv \
    && python -m venv /venv

ENV PATH="/venv/bin:$PATH"

# Copy project dependency definition
COPY pyproject.toml /app/

# Install Python dependencies (including Playwright and its deps)
RUN uv pip install .[docker] --prerelease=allow \
    && playwright install chromium --with-deps

# ====================
# Stage 2: Runtime
# ====================
FROM python:3.12-slim

ARG IMAGE_TAG=dev
ENV IMAGE_TAG=${IMAGE_TAG}

WORKDIR /app

# Install only necessary system dependencies for Chromium to run
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libx11-xcb1 libxcomposite1 libxrandr2 \
    libxdamage1 libgbm1 libasound2 libpangocairo-1.0-0 \
    libatk-bridge2.0-0 libgtk-3-0 fonts-liberation libxshmfence1 \
    libxcb1 xdg-utils netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# Copy the virtual environment and browser binaries from the builder
COPY --from=builder /venv /venv
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Copy Django app code
COPY src/django_project /app/

# Make sure entrypoint script is executable
RUN chmod +x /app/entrypoint.sh

# Expose app port
EXPOSE 8000

# Entrypoint handles DB wait, migrations, and server start
CMD ["./entrypoint.sh"]
