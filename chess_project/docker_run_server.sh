#!/bin/sh
daphne -b 0.0.0.0 -p 8001 chess_project.asgi:application
