import os
import jwt
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# 1. Force Python to find the .env in the parent folder
base_dir = Path(__file__).resolve().parent.parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path)

# 2. Get the key
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# 3. Check if it worked
if not SECRET_KEY:
    print(f"--- DEBUG INFO ---")
    print(f"Looking for .env at: {env_path}")
    print(f"Does file exist? {env_path.exists()}")
    raise ValueError("ERROR: JWT_SECRET_KEY not found. Check your .env file name and content.")

# 4. Generate Token
payload = {
    "user_id": 123,
    "exp": datetime.now(timezone.utc) + timedelta(hours=1)
}

token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
print(f"Generated Token: {token}")