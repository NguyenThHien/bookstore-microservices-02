#!/bin/sh
python manage.py migrate --run-syncdb --noinput
python manage.py runserver 0.0.0.0:8000

