import os

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
application = get_wsgi_application()
