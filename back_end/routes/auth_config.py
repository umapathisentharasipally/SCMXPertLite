import os

# JWT configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "JWT_SECRET_KEY")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY")
RECAPTCHA_VERIFY_URL = os.environ.get("RECAPTCHA_VERIFY_URL")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable must be set")

ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
JWT_ISSUER = os.environ.get("JWT_ISSUER", "scmxpert-lite")

# Collection names from environment
COLL_LOGS = os.getenv('COLL_LOGS', 'logins')
COLL_USERS = os.getenv('COLL_USERS', 'users')