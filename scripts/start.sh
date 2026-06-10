#!/usr/bin/env bash
set -euo pipefail

export DJANGO_SETTINGS_MODULE=myapp.settings
python - <<'PY'
import pymysql
pymysql.install_as_MySQLdb()
PY
python manage.py migrate
python manage.py init_demo

# Use daphne for ASGI/WebSocket support
exec daphne -b 0.0.0.0 -p 8089 myapp.asgi:application
