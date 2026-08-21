#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h db -U shivshakti -d receipts -q 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready."

exec gunicorn --workers=4 --threads=2 --bind=0.0.0.0:5000 app:app
