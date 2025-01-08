#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Function to wait for the database to be ready
wait_for_db() {
  echo "Waiting for database to be ready..."
  until nc -z "$DB_HOST" "$DB_PORT"; do
    echo "Database is unavailable - sleeping"
    sleep 1
  done
  echo "Database is up - continuing"
}

# Wait for the database to be ready
wait_for_db

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Launch gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
