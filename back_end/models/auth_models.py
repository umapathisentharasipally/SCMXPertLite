from pydantic import BaseModel, EmailStr, Field, validator
import re
import smtplib
from dns import resolver

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};:'\"\\|,.<>/?]).{8,}$"
)

def verify_email_deliverability(email: str) -> bool:
    """Check if email is deliverable using SMTP verification."""
    try:
        domain = email.split('@')[1]
        # Check MX records
        mx_records = resolver.resolve(domain, 'MX')
        mx_host = str(mx_records[0].exchange).rstrip('.')
        
        # Try SMTP connection
        server = smtplib.SMTP(mx_host, 25, timeout=10)
        server.helo()
        server.mail('test@example.com')
        code, message = server.rcpt(email)
        server.quit()
        
        return code == 250
    except Exception:
        return False

class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @validator("email")
    def validate_email(cls, email: str) -> str:
        if not verify_email_deliverability(email):
            raise ValueError("Email address is not deliverable or invalid")
        return email

    @validator("password")
    def validate_password(cls, password: str) -> str:
        if not PASSWORD_REGEX.match(password):
            raise ValueError(
                "Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character"
            )
        return password

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
    def validate_password(cls, password: str) -> str:
        if not PASSWORD_REGEX.match(password):
            raise ValueError(
                "Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character"
            )
        return password