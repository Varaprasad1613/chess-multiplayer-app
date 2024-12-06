#!/bin/sh
redis-server --daemonize yes
python3 manage.py runserver 0.0.0.0:80
