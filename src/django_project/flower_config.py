# https://flower.readthedocs.io/en/latest/auth.html
# celery -A core flower --config=flower_config.py

import os

auth = os.environ.get("CELERY_AUTH", "dbslusser@gmail.com")
auth_provider = os.environ.get("CELERY_AUTH_PROVIDER", "flower.views.auth.GoogleAuth2LoginHandler")
oauth2_key = os.environ.get("CELERY_OAUTH2_KEY", "")
oauth2_secret = os.environ.get("CELERY_OAUTH2_SECRET", "")
oauth2_authorize_url = os.environ.get("CELERY_OAUTH2_AUTHORIZE_URL", "")
oauth2_redirect_uri = os.environ.get("CELERY_OAUTH2_REDIRECT_URI", "")
