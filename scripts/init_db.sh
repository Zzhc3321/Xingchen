#!/usr/bin/env bash
set -euo pipefail

export DJANGO_SETTINGS_MODULE=myapp.settings
python - <<'PY'
import pymysql
pymysql.install_as_MySQLdb()
PY
python manage.py makemigrations members chat events
python manage.py migrate
python manage.py init_demo
