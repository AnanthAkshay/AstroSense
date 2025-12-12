"""
Authentication models for AstroSense
Simple email OTP authentication system
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """User model for authentication"""
    id: Optional[int] = None
    email: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_active: bool = True


class Session(BaseModel):
    """Session model for user sessions"""
    id: Optional[int] = None
    user_id: int
    token: str
    created_at: Optional[datetime] = None
    expires_at: datetime
    last_accessed: Optional[datetime] = None
    is_active: bool = True


class OTP(BaseModel):
    """OTP model for temporary storage"""
    email: str
    otp_hash: str
    created_at: Optional[datetime] = None
    expires_at: datetime
    attempts: int = 0


class LoginRequest(BaseModel):
    """Request model for login"""
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    """Request model for OTP verification"""
    email: EmailStr
    otp: str


class AuthResponse(BaseModel):
    """Response model for authentication"""
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None