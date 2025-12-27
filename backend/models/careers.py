"""Career-related Pydantic models"""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class CareerScheduleItem(BaseModel):
    subject: str  # nombre de la materia
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    day: str
    start_time: str
    end_time: str
    mode: str  # "presencial" or "online"
    classroom: Optional[str] = None


class CareerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    modality: str = "presencial"  # presencial, online, hibrido
    schedules: List[CareerScheduleItem] = []


class CareerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    modality: Optional[str] = None
    schedules: Optional[List[CareerScheduleItem]] = None
    is_active: Optional[bool] = None


class CareerResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    career_id: str
    name: str
    description: Optional[str] = None
    modality: str = "presencial"
    schedules: List[dict] = []
    is_active: bool = True
    created_at: str
