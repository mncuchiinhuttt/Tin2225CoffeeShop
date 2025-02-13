#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Run migrations and collect static files
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# Create superuser automatically (if not exists)
python manage.py createsuperuser_auto

# (Optional) Print a success message
echo "Build steps completed."
