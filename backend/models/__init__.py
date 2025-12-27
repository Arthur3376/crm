"""Pydantic models for the application"""
from .users import (
    UserBase, UserCreate, UserLogin, UserUpdate, UserResponse, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest, AdminResetPasswordRequest
)
from .teachers import (
    ScheduleItem, TeacherCreate, TeacherUpdate, TeacherResponse
)
from .careers import (
    CareerScheduleItem, CareerCreate, CareerUpdate, CareerResponse
)
from .students import (
    StudentDocument, AttendanceRecord, StudentCreate, StudentUpdate, StudentResponse,
    ConvertLeadToStudent, CustomFieldDefinition, CustomFieldValue, ChangeRequest, AuditLogEntry
)
from .leads import (
    LeadBase, LeadCreate, LeadUpdate, LeadResponse,
    ConversationMessage, ConversationCreate, ConversationResponse
)
from .appointments import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse
)
from .webhooks import (
    WebhookCreate, WebhookResponse, N8NLeadPayload,
    NotificationSettingsUpdate, NotificationSettingsResponse
)
from .dashboard import DashboardStats
