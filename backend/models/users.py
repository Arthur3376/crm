"""User-related Pydantic models"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "agente"
    phone: Optional[str] = None
    is_active: bool = True
    assigned_careers: List[str] = []


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "agente"
    phone: Optional[str] = None
    assigned_careers: List[str] = []


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    assigned_careers: Optional[List[str]] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    is_active: bool = True
    picture: Optional[str] = None
    assigned_careers: List[str] = []
    created_at: datetime


class TokenResponse(BaseModel):
    token: str
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class AdminResetPasswordRequest(BaseModel):
    new_password: str
