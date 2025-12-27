"""Webhook and notification-related Pydantic models"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime


class WebhookCreate(BaseModel):
    name: str
    url: str
    events: List[str]
    is_active: bool = True


class WebhookResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    webhook_id: str
    name: str
    url: str
    events: List[str]
    is_active: bool
    secret_key: str
    created_at: datetime


# N8N Lead Webhook payload
class N8NLeadPayload(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    career_interest: str
    source: str = "webhook"
    source_detail: Optional[str] = None
    whatsapp_number: Optional[str] = None


# Notification Settings Models
class NotificationSettingsUpdate(BaseModel):
    notification_phone: Optional[str] = None
    notification_webhook_url: Optional[str] = None
    notify_on_new_lead: bool = True
    notify_on_appointment: bool = True
    notify_supervisors: bool = False


class NotificationSettingsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    settings_id: str
    notification_phone: Optional[str] = None
    notification_webhook_url: Optional[str] = None
    notify_on_new_lead: bool = True
    notify_on_appointment: bool = True
    notify_supervisors: bool = False
    updated_at: datetime
