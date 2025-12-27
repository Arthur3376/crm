"""Student-related Pydantic models"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional, Any


class StudentDocument(BaseModel):
    document_id: str
    name: str  # INE, Certificado, Foto, etc.
    filename: str
    uploaded_at: str


class AttendanceRecord(BaseModel):
    date: str
    subject: str
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    status: str  # "presente", "ausente", "justificado"
    notes: Optional[str] = None


class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    career_id: str
    career_name: str
    institutional_email: Optional[str] = None
    lead_id: Optional[str] = None  # Referencia al lead original


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    institutional_email: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    student_id: str
    full_name: str
    email: str
    phone: str
    career_id: str
    career_name: str
    institutional_email: Optional[str] = None
    lead_id: Optional[str] = None
    documents: List[dict] = []
    attendance: List[dict] = []
    custom_fields: dict = {}
    is_active: bool = True
    created_at: str


class ConvertLeadToStudent(BaseModel):
    career_id: str
    career_name: str
    institutional_email: Optional[str] = None


# Custom Fields Models
class CustomFieldDefinition(BaseModel):
    field_id: str
    field_name: str
    field_type: str  # text, number, date, select, checkbox
    options: List[str] = []  # For select type
    required: bool = False
    visible_to_students: bool = True
    editable_by_supervisor: bool = True
    order: int = 0


class CustomFieldValue(BaseModel):
    field_id: str
    value: Any


# Change Request Models (for supervisor approval workflow)
class ChangeRequest(BaseModel):
    request_id: str
    student_id: str
    field_id: str
    field_name: str
    old_value: Any
    new_value: Any
    requested_by_id: str
    requested_by_name: str
    status: str = "pending"  # pending, approved, rejected
    approved_by_id: Optional[str] = None
    approved_by_name: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None


# Audit Log Models
class AuditLogEntry(BaseModel):
    log_id: str
    entity_type: str  # student, lead, etc.
    entity_id: str
    action: str  # create, update, delete, approve, reject
    field_changed: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    performed_by_id: str
    performed_by_name: str
    performed_by_role: str
    authorized_by_id: Optional[str] = None
    authorized_by_name: Optional[str] = None
    timestamp: str
    ip_address: Optional[str] = None
