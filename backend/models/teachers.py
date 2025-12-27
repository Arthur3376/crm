"""Teacher-related Pydantic models"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional


class ScheduleItem(BaseModel):
    day: str  # lunes, martes, etc.
    start_time: str  # "09:00"
    end_time: str  # "11:00"
    mode: str  # "presencial" or "online"
    classroom: Optional[str] = None  # aula o link de zoom


class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subjects: List[str] = []  # materias que imparte


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    subjects: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TeacherResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    teacher_id: str
    name: str
    email: str
    phone: Optional[str] = None
    subjects: List[str] = []
    is_active: bool = True
    created_at: str
