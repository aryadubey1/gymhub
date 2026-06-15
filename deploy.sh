#!/bin/bash

# GymHub Deployment Script

# Pull latest code from git
cd /var/www/gymhub
git pull origin main

# Activate virtualenv
source /var/www/gymhub/venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run collectstatic
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Restart gunicorn via systemd
sudo systemctl restart gymhub

echo "Deployment completed successfully!"
