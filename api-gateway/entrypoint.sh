#!/bin/bash

# Run migrations
python manage.py migrate --noinput

# Start the server
python manage.py runserver 0.0.0.0:8000
