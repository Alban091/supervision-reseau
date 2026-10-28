#!/bin/sh
# Prepare the application, then start the command given by the Dockerfile (gunicorn).
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py ensure_admin

exec "$@"