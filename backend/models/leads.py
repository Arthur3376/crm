"""Lead-related Pydantic models"""
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timezone


class LeadBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    career_interest: str
    source: str = "manual"
    source_detail: Optional[str] = None


class LeadCreate(LeadBase):
    assigned_agent_id: Optional[str] = None


class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    career_interest: Optional[str] = None
    status: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    lead_id: str
    full_name: str
    email: str
    phone: str
    career_interest: str
    source: str
    source_detail: Optional[str] = None
    status: str
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Conversation Models
class ConversationMessage(BaseModel):
    sender: str  # "agent" or "lead"
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationCreate(BaseModel):
    lead_id: str
    message: str
    sender: str = "agent"


class ConversationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    conversation_id: str
    lead_id: str
    messages: List[ConversationMessage]
    created_at: datetime
    updated_at: datetime
