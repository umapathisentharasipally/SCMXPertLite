# zsYctjxntphsXKJkERUoETD-9bVq_x_tskItivJpFqs

import jwt
import datetime
import os 
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

payload = {
    "user_id": "12345", 
    "role": "admin",
    "exp":datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}
token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
print(f"Generated JWT Token: {token}")
try:
    decoded_data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    print(f"Decoded Data: {decoded_data}")
except jwt.ExpiredSignatureError:
    print("Token has expired")
except jwt.InvalidTokenError:
    print("Invalid token")