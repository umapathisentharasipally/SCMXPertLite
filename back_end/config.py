import os
from dotenv import load_dotenv
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent

load_dotenv(dotenv_path=ROOT_DIR / '.env')


# Database Configuration
MONGO_USERNAME = os.getenv('MONGO_USERNAME')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_CLUSTER_NAME = os.getenv('MONGO_CLUSTER_NAME')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
MONGO_URL = os.getenv('MONGO_URL')


# Collection Names
COLL_USERS = os.getenv('COLL_USERS', 'users')
COLL_SHIPMENTS = os.getenv('COLL_SHIPMENTS', 'shipments')
COLL_LOGS = os.getenv('COLL_LOGS', 'logins')
COLL_DEVICES = os.getenv('COLL_DEVICES', 'devices')


# JWT Configuration
SECRET_KEY = os.getenv('SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")


ALGORITHM = 'HS256'
JWT_ISSUER = 'scmxpertlite'


# reCAPTCHA
RECAPTCHA_SECRET = os.getenv('RECAPTCHA_SECRET_KEY')

if not RECAPTCHA_SECRET:
    raise ValueError("RECAPTCHA_SECRET_KEY environment variable is required")


RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY')

if not RECAPTCHA_SITE_KEY:
    raise ValueError("RECAPTCHA_SITE_KEY environment variable is required")


RECAPTCHA_VERIFY_URL = (
    "https://www.google.com/recaptcha/api/siteverify"
)