from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime
from dns import resolver
import re


PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};:'\"\\|,.<>/?]).{8,}$"
)

PHONE_REGEX = re.compile(
    r"^[6-9]\d{9}$"
)

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "guerrillamail.com",
    "tempmail.com",
    "temp-mail.org",
    "yopmail.com",
    "throwawaymail.com",
    "sharklasers.com",
    "getnada.com",
    "trashmail.com",
    "dispostable.com",
    "fakeinbox.com",
    "maildrop.cc"
}


def verify_email_domain(email: str) -> bool:
    try:
        domain = email.split("@")[1]

        dns_resolver = resolver.Resolver()
        dns_resolver.lifetime = 3
        dns_resolver.timeout = 3

        mx_records = dns_resolver.resolve(domain, "MX")

        return len(mx_records) > 0

    except Exception:
        return False

class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=10)
    password: str = Field(..., min_length=8, max_length=64)
    confirm_password: str = Field(..., min_length=8, max_length=64)
   # recaptcha_token: str = Field(..., min_length=1)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 3:
            raise ValueError("Full name must be at least 3 characters")

        return value

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, email: str) -> str:
        email = email.lower().strip()
        domain = email.split("@")[1]

        if domain in DISPOSABLE_DOMAINS:
            raise ValueError("Temporary or disposable email addresses are not allowed")

        if not verify_email_domain(email):
            raise ValueError("Invalid email domain or domain does not exist")

        return email
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        value = value.strip()

        if not PHONE_REGEX.match(value):
            raise ValueError(
                "Invalid Indian phone number"
            )

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if not PASSWORD_REGEX.match(password):
            raise ValueError(
                "Password must include uppercase, lowercase, digit, and special character"
            )

        return password
    
    @model_validator(mode="after")
    def validate_confirm_password(self):
        if self.password != self.confirm_password:
            raise ValueError(
                "Password and confirm password do not match"
            )

        return self


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
   # recaptcha_token: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=64)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, password: str) -> str:
        if not PASSWORD_REGEX.match(password):
            raise ValueError(
                "Password must include uppercase, lowercase, digit, and special character"
            )

        return password