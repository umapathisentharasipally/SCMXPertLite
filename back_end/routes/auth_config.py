import os
from dotenv import load_dotenv

load_dotenv()

# Collection names
COLL_USERS = os.getenv("COLL_USERS", "users")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
JWT_ISSUER = "scmxpertlite"