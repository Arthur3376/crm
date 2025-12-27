"""Appointment-related Pydantic models"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AppointmentCreate(BaseModel):
    lead_id: str
    agent_id: str
    title: str
    description: Optional[str] = None
    scheduled_at: datetime


class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    appointment_id: str
    lead_id: str
    lead_name: Optional[str] = None
    agent_id: str
    agent_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    status: str
    created_at: datetime
