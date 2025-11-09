from datetime import datetime, timedelta

# Token options
TOKEN_SECRET = "supersecretkey"
TOKEN_ALGORITHM = "HS256"
AUTH_FLOW_EXPIRATION = timedelta(minutes=3)
ACCESS_TOKEN_EXPIRATION = timedelta(minutes=30)
REFRESH_TOKEN_EXPIRATION = timedelta(days=60)

# Logic options
LOGIN_AFTER_REGISTRATION = False