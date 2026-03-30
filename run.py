import bcrypt
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr

password = str(input("enter your password:"))
plain_password = "Umapathi@123"

def hash_password(password: str) -> str:
    """Hash a password using bcrypt """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

print("hashed password:", hash_password(password))

def verify_password(plain_password:str, hashed_password:str) ->bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'),hashed_password.encode('utf-8'))

print("verify password:", verify_password(plain_password, hash_password(password)))