from fastapi import APIRouter, HTTPException, status, Depends
import os
import jwt
from typing import Optional
from datetime import datetime, timedelta, timezone
import bcrypt

user_id = str(input("Enter user ID: "))
user_email = str(input("Enter user email: "))

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data:dict, expires_delta:Optional[timedelta] =None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.now(timezone.utc)+ timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)   # issued at
    })
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt


token = create_access_token({
    "sub": user_id,
    "email": user_email
})

print("Generated JWT Token:", token)
