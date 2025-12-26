from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import httpx
import resend
from twilio.rest import Client as TwilioClient
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'leadflow-pro-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")

# Google Calendar Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/userinfo.email"]

# Resend Email Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
    logger.info("Resend email client configured")

# Create the main app
app = FastAPI(title="UCIC API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============== ENUMS & CONSTANTS ==============
USER_ROLES = ["admin", "gerente", "supervisor", "agente", "maestro"]
LEAD_SOURCES = ["facebook", "instagram", "tiktok", "manual", "webhook"]
LEAD_STATUSES = ["etapa_1_informacion", "etapa_2_contacto", "etapa_3_documentacion", "etapa_4_inscrito"]
DEFAULT_CAREERS = ["Ingeniería", "Medicina", "Derecho", "Administración", "Contabilidad", "Psicología", "Diseño", "Marketing", "Otra"]
NOTIFICATION_EVENTS = ["lead.created", "lead.updated", "appointment.created", "appointment.reminder"]

# ============== PYDANTIC MODELS ==============

# User Models
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

# Password Reset Models
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class AdminResetPasswordRequest(BaseModel):
    new_password: str

# Teacher Models
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
    created_at: datetime

# Career Schedule Models
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
    created_at: datetime

# Student Models
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
    is_active: bool = True
    created_at: datetime

class ConvertLeadToStudent(BaseModel):
    career_id: str
    career_name: str
    institutional_email: Optional[str] = None

# Lead Models
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

# Appointment Models
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

# Webhook Models
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

# Dashboard Models
class DashboardStats(BaseModel):
    total_leads: int
    leads_by_status: dict
    leads_by_source: dict
    leads_by_career: dict
    leads_by_agent: dict
    conversion_rate: float
    new_leads_today: int
    appointments_today: int

# ============== HELPER FUNCTIONS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(request: Request) -> dict:
    # Check cookie first (Google Auth)
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one(
            {"session_token": session_token},
            {"_id": 0}
        )
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one(
                    {"user_id": session["user_id"]},
                    {"_id": 0}
                )
                if user:
                    return user
    
    # Check Authorization header (JWT)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_jwt_token(token)
        user = await db.users.find_one(
            {"user_id": payload["user_id"]},
            {"_id": 0}
        )
        if user:
            return user
    
    raise HTTPException(status_code=401, detail="No autenticado")

def require_roles(allowed_roles: List[str]):
    async def role_checker(request: Request):
        user = await get_current_user(request)
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return user
    return role_checker

async def find_agent_for_career(career: str) -> Optional[dict]:
    """Find an available agent assigned to handle the given career"""
    # Find agents with this career assigned, ordered by lead count (load balancing)
    agents = await db.users.find({
        "role": "agente",
        "is_active": True,
        "assigned_careers": career
    }, {"_id": 0}).to_list(100)
    
    if not agents:
        # If no agent has this career, return None (will use default assignment)
        return None
    
    # Simple load balancing: count leads per agent and assign to the one with fewer leads
    agent_lead_counts = []
    for agent in agents:
        lead_count = await db.leads.count_documents({"assigned_agent_id": agent["user_id"]})
        agent_lead_counts.append((agent, lead_count))
    
    # Sort by lead count (ascending) and return the agent with fewer leads
    agent_lead_counts.sort(key=lambda x: x[1])
    return agent_lead_counts[0][0] if agent_lead_counts else None

# ============== AUTH ENDPOINTS ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role,
        "phone": user_data.phone,
        "is_active": True,
        "picture": None,
        "assigned_careers": user_data.assigned_careers,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_jwt_token(user_id, user_data.email, user_data.role)
    user_response = UserResponse(
        user_id=user_id,
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        phone=user_data.phone,
        is_active=True,
        picture=None,
        assigned_careers=user_data.assigned_careers,
        created_at=datetime.fromisoformat(user_doc["created_at"])
    )
    
    return TokenResponse(token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Usuario desactivado")
    
    token = create_jwt_token(user["user_id"], user["email"], user["role"])
    
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    user_response = UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        phone=user.get("phone"),
        is_active=user.get("is_active", True),
        picture=user.get("picture"),
        assigned_careers=user.get("assigned_careers", []),
        created_at=created_at
    )
    
    return TokenResponse(token=token, user=user_response)

@api_router.post("/auth/forgot-password")
async def forgot_password(request_data: ForgotPasswordRequest):
    """Send password reset email"""
    user = await db.users.find_one({"email": request_data.email}, {"_id": 0})
    
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "Si el email existe, recibirás un enlace de recuperación"}
    
    # Generate reset token
    reset_token = f"reset_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Save token to database
    await db.password_resets.delete_many({"email": request_data.email})  # Remove old tokens
    await db.password_resets.insert_one({
        "email": request_data.email,
        "token": reset_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send email with Resend
    if RESEND_API_KEY:
        frontend_url = os.environ.get('FRONTEND_URL', 'https://leadsync-16.preview.emergentagent.com')
        reset_link = f"{frontend_url}/forgot-password?token={reset_token}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e293b; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">UCIC</h1>
            </div>
            <div style="padding: 30px; background: #f8fafc;">
                <h2 style="color: #1e293b;">Recupera tu contraseña</h2>
                <p style="color: #64748b;">Hola {user.get('name', '')},</p>
                <p style="color: #64748b;">Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
                <p style="color: #64748b;">Haz clic en el siguiente botón para crear una nueva contraseña:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background: #1e293b; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Restablecer Contraseña
                    </a>
                </div>
                <p style="color: #64748b; font-size: 14px;">Este enlace expirará en 1 hora.</p>
                <p style="color: #64748b; font-size: 14px;">Si no solicitaste este cambio, puedes ignorar este email.</p>
            </div>
            <div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 12px;">
                © 2024 UCIC. Todos los derechos reservados.
            </div>
        </div>
        """
        
        try:
            params = {
                "from": SENDER_EMAIL,
                "to": [request_data.email],
                "subject": "Recupera tu contraseña - UCIC",
                "html": html_content
            }
            await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Password reset email sent to {request_data.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            raise HTTPException(status_code=500, detail="Error al enviar el email")
    else:
        logger.warning("Resend API key not configured, cannot send password reset email")
        raise HTTPException(status_code=500, detail="El servicio de email no está configurado")
    
    return {"message": "Si el email existe, recibirás un enlace de recuperación"}

@api_router.post("/auth/reset-password")
async def reset_password(request_data: ResetPasswordRequest):
    """Reset password using token"""
    # Find token
    reset_record = await db.password_resets.find_one({"token": request_data.token}, {"_id": 0})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    # Check expiration
    expires_at = datetime.fromisoformat(reset_record["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if datetime.now(timezone.utc) > expires_at:
        await db.password_resets.delete_one({"token": request_data.token})
        raise HTTPException(status_code=400, detail="Token expirado")
    
    # Validate password
    if len(request_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    # Update password
    new_hash = hash_password(request_data.new_password)
    result = await db.users.update_one(
        {"email": reset_record["email"]},
        {"$set": {"password_hash": new_hash}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Delete used token
    await db.password_resets.delete_one({"token": request_data.token})
    
    logger.info(f"Password reset successful for {reset_record['email']}")
    return {"message": "Contraseña actualizada exitosamente"}

@api_router.post("/users/{user_id}/reset-password")
async def admin_reset_password(user_id: str, request_data: AdminResetPasswordRequest, request: Request):
    """Admin endpoint to reset user password"""
    current_user = await get_current_user(request)
    
    # Only admin can reset passwords
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden resetear contraseñas")
    
    # Validate password
    if len(request_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    # Check user exists
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Update password
    new_hash = hash_password(request_data.new_password)
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"password_hash": new_hash}}
    )
    
    logger.info(f"Admin {current_user['email']} reset password for user {user_id}")
    return {"message": "Contraseña actualizada exitosamente"}

@api_router.post("/auth/session")
async def process_google_session(request: Request, response: Response):
    """Process Google OAuth session from Emergent Auth"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id requerido")
    
    # Get user data from Emergent Auth
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Sesión inválida")
        
        auth_data = auth_response.json()
    
    email = auth_data.get("email")
    name = auth_data.get("name")
    picture = auth_data.get("picture")
    session_token = auth_data.get("session_token")
    
    # Find or create user
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user info if needed
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture}}
        )
        role = existing_user["role"]
        created_at = existing_user.get("created_at")
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "password_hash": "",
            "role": "agente",  # Default role for new Google users
            "phone": None,
            "is_active": True,
            "picture": picture,
            "created_at": now
        }
        await db.users.insert_one(user_doc)
        role = "agente"
        created_at = now
    
    # Store session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "role": role,
        "picture": picture,
        "created_at": created_at.isoformat()
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(request: Request):
    user = await get_current_user(request)
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        phone=user.get("phone"),
        is_active=user.get("is_active", True),
        picture=user.get("picture"),
        created_at=created_at
    )

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    return {"message": "Sesión cerrada exitosamente"}

# ============== USER MANAGEMENT ENDPOINTS ==============

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(request: Request):
    current_user = await require_roles(["admin", "gerente"])(request)
    
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    result = []
    for user in users:
        created_at = user.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            phone=user.get("phone"),
            is_active=user.get("is_active", True),
            picture=user.get("picture"),
            assigned_careers=user.get("assigned_careers", []),
            created_at=created_at
        ))
    return result

@api_router.get("/users/agents", response_model=List[UserResponse])
async def get_agents(request: Request):
    await get_current_user(request)
    
    users = await db.users.find(
        {"role": "agente", "is_active": True},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    result = []
    for user in users:
        created_at = user.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            phone=user.get("phone"),
            is_active=user.get("is_active", True),
            picture=user.get("picture"),
            assigned_careers=user.get("assigned_careers", []),
            created_at=created_at
        ))
    return result

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        phone=user.get("phone"),
        is_active=user.get("is_active", True),
        picture=user.get("picture"),
        assigned_careers=user.get("assigned_careers", []),
        created_at=created_at
    )

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, update_data: UserUpdate, request: Request):
    current_user = await require_roles(["admin", "gerente"])(request)
    
    # Only admin can change roles
    if update_data.role and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede cambiar roles")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    created_at = user.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        phone=user.get("phone"),
        is_active=user.get("is_active", True),
        picture=user.get("picture"),
        assigned_careers=user.get("assigned_careers", []),
        created_at=created_at
    )

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    await require_roles(["admin"])(request)
    
    result = await db.users.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Usuario eliminado"}

# ============== TEACHER ENDPOINTS ==============

@api_router.post("/teachers", response_model=TeacherResponse)
async def create_teacher(teacher_data: TeacherCreate, request: Request):
    """Create a new teacher"""
    await require_roles(["admin", "gerente"])(request)
    
    # Check if email already exists
    existing = await db.teachers.find_one({"email": teacher_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    teacher_id = f"teacher_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    teacher = {
        "teacher_id": teacher_id,
        "name": teacher_data.name,
        "email": teacher_data.email,
        "phone": teacher_data.phone,
        "subjects": teacher_data.subjects,
        "is_active": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.teachers.insert_one(teacher)
    teacher.pop("_id", None)
    
    logger.info(f"Teacher created: {teacher_id}")
    return TeacherResponse(**teacher, created_at=now)

@api_router.get("/teachers", response_model=List[TeacherResponse])
async def get_teachers(request: Request):
    """Get all teachers"""
    await get_current_user(request)
    
    teachers = await db.teachers.find({}, {"_id": 0}).to_list(1000)
    return [TeacherResponse(**t, created_at=datetime.fromisoformat(t["created_at"])) for t in teachers]

@api_router.get("/teachers/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(teacher_id: str, request: Request):
    """Get a single teacher"""
    await get_current_user(request)
    
    teacher = await db.teachers.find_one({"teacher_id": teacher_id}, {"_id": 0})
    if not teacher:
        raise HTTPException(status_code=404, detail="Maestro no encontrado")
    
    return TeacherResponse(**teacher, created_at=datetime.fromisoformat(teacher["created_at"]))

@api_router.put("/teachers/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(teacher_id: str, teacher_data: TeacherUpdate, request: Request):
    """Update a teacher"""
    await require_roles(["admin", "gerente"])(request)
    
    teacher = await db.teachers.find_one({"teacher_id": teacher_id}, {"_id": 0})
    if not teacher:
        raise HTTPException(status_code=404, detail="Maestro no encontrado")
    
    update_data = {k: v for k, v in teacher_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.teachers.update_one({"teacher_id": teacher_id}, {"$set": update_data})
    
    updated_teacher = await db.teachers.find_one({"teacher_id": teacher_id}, {"_id": 0})
    return TeacherResponse(**updated_teacher, created_at=datetime.fromisoformat(updated_teacher["created_at"]))

@api_router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: str, request: Request):
    """Delete a teacher"""
    await require_roles(["admin"])(request)
    
    result = await db.teachers.delete_one({"teacher_id": teacher_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Maestro no encontrado")
    
    return {"message": "Maestro eliminado"}

# ============== CAREER MANAGEMENT ENDPOINTS ==============

@api_router.post("/careers/full", response_model=CareerResponse)
async def create_career_full(career_data: CareerCreate, request: Request):
    """Create a career with schedules"""
    await require_roles(["admin", "gerente"])(request)
    
    # Check if career name already exists
    existing = await db.careers_full.find_one({"name": career_data.name}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="La carrera ya existe")
    
    career_id = f"career_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Process schedules to add teacher names
    schedules = []
    for schedule in career_data.schedules:
        schedule_dict = schedule.model_dump()
        if schedule.teacher_id:
            teacher = await db.teachers.find_one({"teacher_id": schedule.teacher_id}, {"_id": 0})
            if teacher:
                schedule_dict["teacher_name"] = teacher["name"]
        schedules.append(schedule_dict)
    
    career = {
        "career_id": career_id,
        "name": career_data.name,
        "description": career_data.description,
        "modality": career_data.modality,
        "schedules": schedules,
        "is_active": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.careers_full.insert_one(career)
    career.pop("_id", None)
    
    # Also add to the simple careers list if not exists
    careers_doc = await db.settings.find_one({"type": "careers"}, {"_id": 0})
    if careers_doc and career_data.name not in careers_doc.get("items", []):
        await db.settings.update_one(
            {"type": "careers"},
            {"$push": {"items": career_data.name}}
        )
    
    logger.info(f"Career created: {career_id}")
    return CareerResponse(**career, created_at=now)

@api_router.get("/careers/full", response_model=List[CareerResponse])
async def get_careers_full(request: Request):
    """Get all careers with schedules"""
    await get_current_user(request)
    
    careers = await db.careers_full.find({}, {"_id": 0}).to_list(1000)
    return [CareerResponse(**c, created_at=datetime.fromisoformat(c["created_at"])) for c in careers]

@api_router.get("/careers/full/{career_id}", response_model=CareerResponse)
async def get_career_full(career_id: str, request: Request):
    """Get a single career with schedules"""
    await get_current_user(request)
    
    career = await db.careers_full.find_one({"career_id": career_id}, {"_id": 0})
    if not career:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    
    return CareerResponse(**career, created_at=datetime.fromisoformat(career["created_at"]))

@api_router.put("/careers/full/{career_id}", response_model=CareerResponse)
async def update_career_full(career_id: str, career_data: CareerUpdate, request: Request):
    """Update a career"""
    await require_roles(["admin", "gerente"])(request)
    
    career = await db.careers_full.find_one({"career_id": career_id}, {"_id": 0})
    if not career:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    
    update_data = {}
    for k, v in career_data.model_dump().items():
        if v is not None:
            if k == "schedules":
                # Process schedules to add teacher names
                schedules = []
                for schedule in v:
                    schedule_dict = schedule if isinstance(schedule, dict) else schedule.model_dump()
                    if schedule_dict.get("teacher_id"):
                        teacher = await db.teachers.find_one({"teacher_id": schedule_dict["teacher_id"]}, {"_id": 0})
                        if teacher:
                            schedule_dict["teacher_name"] = teacher["name"]
                    schedules.append(schedule_dict)
                update_data["schedules"] = schedules
            else:
                update_data[k] = v
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.careers_full.update_one({"career_id": career_id}, {"$set": update_data})
    
    updated_career = await db.careers_full.find_one({"career_id": career_id}, {"_id": 0})
    return CareerResponse(**updated_career, created_at=datetime.fromisoformat(updated_career["created_at"]))

@api_router.delete("/careers/full/{career_id}")
async def delete_career_full(career_id: str, request: Request):
    """Delete a career"""
    await require_roles(["admin"])(request)
    
    career = await db.careers_full.find_one({"career_id": career_id}, {"_id": 0})
    if not career:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    
    # Remove from simple careers list
    await db.settings.update_one(
        {"type": "careers"},
        {"$pull": {"items": career["name"]}}
    )
    
    result = await db.careers_full.delete_one({"career_id": career_id})
    
    return {"message": "Carrera eliminada"}

# ============== STUDENT ENDPOINTS ==============

STUDENT_DOCUMENTS_PATH = Path("/app/student_documents")
STUDENT_DOCUMENTS_PATH.mkdir(exist_ok=True)

@api_router.post("/students", response_model=StudentResponse)
async def create_student(student_data: StudentCreate, request: Request):
    """Create a new student directly"""
    await require_roles(["admin", "gerente"])(request)
    
    student_id = f"student_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Create student document folder
    student_folder = STUDENT_DOCUMENTS_PATH / student_id
    student_folder.mkdir(exist_ok=True)
    
    student = {
        "student_id": student_id,
        "full_name": student_data.full_name,
        "email": student_data.email,
        "phone": student_data.phone,
        "career_id": student_data.career_id,
        "career_name": student_data.career_name,
        "institutional_email": student_data.institutional_email,
        "lead_id": student_data.lead_id,
        "documents": [],
        "attendance": [],
        "is_active": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.students.insert_one(student)
    student.pop("_id", None)
    
    logger.info(f"Student created: {student_id}")
    return StudentResponse(**student, created_at=now)

@api_router.post("/leads/{lead_id}/convert-to-student", response_model=StudentResponse)
async def convert_lead_to_student(lead_id: str, data: ConvertLeadToStudent, request: Request):
    """Convert a lead (at stage 4) to a student"""
    await require_roles(["admin", "gerente"])(request)
    
    # Get the lead
    lead = await db.leads.find_one({"lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    # Check if lead is at stage 4
    if lead.get("status") != "etapa_4_inscrito":
        raise HTTPException(status_code=400, detail="El lead debe estar en Etapa 4 - Inscrito para convertirse en estudiante")
    
    # Check if student already exists for this lead
    existing = await db.students.find_one({"lead_id": lead_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Este lead ya fue convertido en estudiante")
    
    student_id = f"student_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Create student document folder
    student_folder = STUDENT_DOCUMENTS_PATH / student_id
    student_folder.mkdir(exist_ok=True)
    
    student = {
        "student_id": student_id,
        "full_name": lead["full_name"],
        "email": lead["email"],
        "phone": lead["phone"],
        "career_id": data.career_id,
        "career_name": data.career_name,
        "institutional_email": data.institutional_email,
        "lead_id": lead_id,
        "documents": [],
        "attendance": [],
        "is_active": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.students.insert_one(student)
    student.pop("_id", None)
    
    # Update lead status to indicate conversion
    await db.leads.update_one(
        {"lead_id": lead_id},
        {"$set": {"converted_to_student": True, "student_id": student_id}}
    )
    
    logger.info(f"Lead {lead_id} converted to student {student_id}")
    return StudentResponse(**student, created_at=now)

@api_router.get("/students", response_model=List[StudentResponse])
async def get_students(request: Request):
    """Get all students"""
    await get_current_user(request)
    
    students = await db.students.find({}, {"_id": 0}).to_list(1000)
    return [StudentResponse(**s, created_at=datetime.fromisoformat(s["created_at"])) for s in students]

@api_router.get("/students/{student_id}", response_model=StudentResponse)
async def get_student(student_id: str, request: Request):
    """Get a single student"""
    await get_current_user(request)
    
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    return StudentResponse(**student, created_at=datetime.fromisoformat(student["created_at"]))

@api_router.put("/students/{student_id}", response_model=StudentResponse)
async def update_student(student_id: str, student_data: StudentUpdate, request: Request):
    """Update a student"""
    await require_roles(["admin", "gerente"])(request)
    
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    update_data = {k: v for k, v in student_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.students.update_one({"student_id": student_id}, {"$set": update_data})
    
    updated_student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    return StudentResponse(**updated_student, created_at=datetime.fromisoformat(updated_student["created_at"]))

@api_router.delete("/students/{student_id}")
async def delete_student(student_id: str, request: Request):
    """Delete a student"""
    await require_roles(["admin"])(request)
    
    result = await db.students.delete_one({"student_id": student_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Optionally delete the documents folder
    student_folder = STUDENT_DOCUMENTS_PATH / student_id
    if student_folder.exists():
        import shutil
        shutil.rmtree(student_folder)
    
    return {"message": "Estudiante eliminado"}

# Document upload endpoints
from fastapi import UploadFile, File

@api_router.post("/students/{student_id}/documents")
async def upload_student_document(
    student_id: str, 
    document_type: str,
    file: UploadFile = File(...),
    request: Request = None
):
    """Upload a document for a student"""
    await require_roles(["admin", "gerente"])(request)
    
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Validate file type
    allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(allowed_extensions)}")
    
    # Create document ID and save file
    document_id = f"doc_{uuid.uuid4().hex[:8]}"
    student_folder = STUDENT_DOCUMENTS_PATH / student_id
    student_folder.mkdir(exist_ok=True)
    
    safe_filename = f"{document_id}_{file.filename}"
    file_path = student_folder / safe_filename
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Add document to student record
    now = datetime.now(timezone.utc)
    document = {
        "document_id": document_id,
        "name": document_type,
        "filename": safe_filename,
        "original_filename": file.filename,
        "uploaded_at": now.isoformat()
    }
    
    await db.students.update_one(
        {"student_id": student_id},
        {"$push": {"documents": document}, "$set": {"updated_at": now.isoformat()}}
    )
    
    logger.info(f"Document {document_id} uploaded for student {student_id}")
    return {"message": "Documento subido exitosamente", "document": document}

@api_router.delete("/students/{student_id}/documents/{document_id}")
async def delete_student_document(student_id: str, document_id: str, request: Request):
    """Delete a student document"""
    await require_roles(["admin", "gerente"])(request)
    
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Find and remove document
    document = None
    for doc in student.get("documents", []):
        if doc["document_id"] == document_id:
            document = doc
            break
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Delete file
    file_path = STUDENT_DOCUMENTS_PATH / student_id / document["filename"]
    if file_path.exists():
        file_path.unlink()
    
    # Remove from database
    await db.students.update_one(
        {"student_id": student_id},
        {"$pull": {"documents": {"document_id": document_id}}}
    )
    
    return {"message": "Documento eliminado"}

# Attendance endpoints
@api_router.post("/students/{student_id}/attendance")
async def record_attendance(student_id: str, request: Request):
    """Record attendance for a student"""
    await require_roles(["admin", "gerente", "maestro"])(request)
    
    body = await request.json()
    
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    now = datetime.now(timezone.utc)
    attendance_record = {
        "attendance_id": f"att_{uuid.uuid4().hex[:8]}",
        "date": body.get("date", now.strftime("%Y-%m-%d")),
        "subject": body.get("subject", ""),
        "teacher_id": body.get("teacher_id"),
        "teacher_name": body.get("teacher_name"),
        "status": body.get("status", "presente"),  # presente, ausente, justificado
        "notes": body.get("notes"),
        "recorded_at": now.isoformat()
    }
    
    await db.students.update_one(
        {"student_id": student_id},
        {"$push": {"attendance": attendance_record}, "$set": {"updated_at": now.isoformat()}}
    )
    
    return {"message": "Asistencia registrada", "attendance": attendance_record}

@api_router.get("/students/{student_id}/attendance")
async def get_student_attendance(student_id: str, request: Request):
    """Get attendance records for a student"""
    await get_current_user(request)
    
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    return {"attendance": student.get("attendance", [])}

@api_router.get("/students/{student_id}/documents-folder")
async def get_student_documents_folder(student_id: str, request: Request):
    """Get the path to student's documents folder"""
    await require_roles(["admin", "gerente"])(request)
    
    student = await db.students.find_one({"student_id": student_id}, {"_id": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    folder_path = STUDENT_DOCUMENTS_PATH / student_id
    return {
        "folder_path": str(folder_path),
        "vpn_note": "Para acceso VPN, configura tu servidor VPN para exponer /app/student_documents/"
    }

# ============== LEAD ENDPOINTS ==============

@api_router.post("/leads", response_model=LeadResponse)
async def create_lead(lead_data: LeadCreate, request: Request):
    current_user = await get_current_user(request)
    
    lead_id = f"lead_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    # Determine agent assignment
    assigned_agent_id = lead_data.assigned_agent_id
    
    # If no agent specified, try to find one based on career
    if not assigned_agent_id:
        career_agent = await find_agent_for_career(lead_data.career_interest)
        if career_agent:
            assigned_agent_id = career_agent["user_id"]
        else:
            # Fallback to current user if they are an agent, otherwise leave unassigned
            if current_user["role"] == "agente":
                assigned_agent_id = current_user["user_id"]
    
    lead_doc = {
        "lead_id": lead_id,
        "full_name": lead_data.full_name,
        "email": lead_data.email,
        "phone": lead_data.phone,
        "career_interest": lead_data.career_interest,
        "source": lead_data.source,
        "source_detail": lead_data.source_detail,
        "status": "nuevo",
        "assigned_agent_id": assigned_agent_id,
        "notes": None,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["user_id"]
    }
    
    await db.leads.insert_one(lead_doc)
    
    # Get agent name
    agent_name = None
    agent_data = None
    if lead_doc["assigned_agent_id"]:
        agent = await db.users.find_one({"user_id": lead_doc["assigned_agent_id"]}, {"_id": 0})
        if agent:
            agent_name = agent["name"]
            agent_data = {"name": agent["name"], "email": agent.get("email"), "phone": agent.get("phone")}
    
    # Send notification for new lead
    await send_notification("lead.created", {
        "lead_id": lead_id,
        "full_name": lead_data.full_name,
        "email": lead_data.email,
        "phone": lead_data.phone,
        "career_interest": lead_data.career_interest,
        "source": lead_data.source,
        "source_detail": lead_data.source_detail
    }, agent_data)
    
    return LeadResponse(
        lead_id=lead_id,
        full_name=lead_data.full_name,
        email=lead_data.email,
        phone=lead_data.phone,
        career_interest=lead_data.career_interest,
        source=lead_data.source,
        source_detail=lead_data.source_detail,
        status="nuevo",
        assigned_agent_id=lead_doc["assigned_agent_id"],
        assigned_agent_name=agent_name,
        notes=None,
        created_at=datetime.fromisoformat(now),
        updated_at=datetime.fromisoformat(now)
    )

@api_router.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    request: Request,
    status: Optional[str] = None,
    source: Optional[str] = None,
    agent_id: Optional[str] = None,
    career: Optional[str] = None,
    search: Optional[str] = None
):
    current_user = await get_current_user(request)
    
    query = {}
    
    # Role-based filtering
    if current_user["role"] == "agente":
        query["assigned_agent_id"] = current_user["user_id"]
    elif current_user["role"] == "supervisor" and agent_id:
        query["assigned_agent_id"] = agent_id
    elif agent_id:
        query["assigned_agent_id"] = agent_id
    
    if status:
        query["status"] = status
    if source:
        query["source"] = source
    if career:
        query["career_interest"] = career
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
    
    leads = await db.leads.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Get all agent names
    agent_ids = list(set([l.get("assigned_agent_id") for l in leads if l.get("assigned_agent_id")]))
    agents = await db.users.find({"user_id": {"$in": agent_ids}}, {"_id": 0}).to_list(1000)
    agent_map = {a["user_id"]: a["name"] for a in agents}
    
    result = []
    for lead in leads:
        created_at = lead.get("created_at")
        updated_at = lead.get("updated_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        result.append(LeadResponse(
            lead_id=lead["lead_id"],
            full_name=lead["full_name"],
            email=lead["email"],
            phone=lead["phone"],
            career_interest=lead["career_interest"],
            source=lead["source"],
            source_detail=lead.get("source_detail"),
            status=lead["status"],
            assigned_agent_id=lead.get("assigned_agent_id"),
            assigned_agent_name=agent_map.get(lead.get("assigned_agent_id")),
            notes=lead.get("notes"),
            created_at=created_at,
            updated_at=updated_at
        ))
    
    return result

@api_router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str, request: Request):
    await get_current_user(request)
    
    lead = await db.leads.find_one({"lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    agent_name = None
    if lead.get("assigned_agent_id"):
        agent = await db.users.find_one({"user_id": lead["assigned_agent_id"]}, {"_id": 0})
        if agent:
            agent_name = agent["name"]
    
    created_at = lead.get("created_at")
    updated_at = lead.get("updated_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    return LeadResponse(
        lead_id=lead["lead_id"],
        full_name=lead["full_name"],
        email=lead["email"],
        phone=lead["phone"],
        career_interest=lead["career_interest"],
        source=lead["source"],
        source_detail=lead.get("source_detail"),
        status=lead["status"],
        assigned_agent_id=lead.get("assigned_agent_id"),
        assigned_agent_name=agent_name,
        notes=lead.get("notes"),
        created_at=created_at,
        updated_at=updated_at
    )

@api_router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: str, update_data: LeadUpdate, request: Request):
    await get_current_user(request)
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.leads.update_one(
        {"lead_id": lead_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    return await get_lead(lead_id, request)

@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    result = await db.leads.delete_one({"lead_id": lead_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    # Also delete related conversations
    await db.conversations.delete_many({"lead_id": lead_id})
    
    return {"message": "Lead eliminado"}

# ============== CONVERSATION ENDPOINTS ==============

@api_router.post("/conversations", response_model=ConversationResponse)
async def add_conversation_message(conv_data: ConversationCreate, request: Request):
    current_user = await get_current_user(request)
    
    now = datetime.now(timezone.utc)
    message = {
        "sender": conv_data.sender,
        "message": conv_data.message,
        "timestamp": now.isoformat(),
        "user_id": current_user["user_id"],
        "user_name": current_user["name"]
    }
    
    # Find existing conversation or create new
    existing = await db.conversations.find_one({"lead_id": conv_data.lead_id}, {"_id": 0})
    
    if existing:
        await db.conversations.update_one(
            {"lead_id": conv_data.lead_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": now.isoformat()}
            }
        )
        conv_id = existing["conversation_id"]
    else:
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        conv_doc = {
            "conversation_id": conv_id,
            "lead_id": conv_data.lead_id,
            "messages": [message],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        await db.conversations.insert_one(conv_doc)
    
    return await get_conversation(conv_data.lead_id, request)

@api_router.get("/conversations/{lead_id}", response_model=ConversationResponse)
async def get_conversation(lead_id: str, request: Request):
    await get_current_user(request)
    
    conv = await db.conversations.find_one({"lead_id": lead_id}, {"_id": 0})
    if not conv:
        # Return empty conversation
        now = datetime.now(timezone.utc)
        return ConversationResponse(
            conversation_id=f"conv_{uuid.uuid4().hex[:12]}",
            lead_id=lead_id,
            messages=[],
            created_at=now,
            updated_at=now
        )
    
    messages = []
    for msg in conv.get("messages", []):
        ts = msg.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        messages.append(ConversationMessage(
            sender=msg["sender"],
            message=msg["message"],
            timestamp=ts
        ))
    
    created_at = conv.get("created_at")
    updated_at = conv.get("updated_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    return ConversationResponse(
        conversation_id=conv["conversation_id"],
        lead_id=lead_id,
        messages=messages,
        created_at=created_at,
        updated_at=updated_at
    )

# ============== APPOINTMENT ENDPOINTS ==============

@api_router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(apt_data: AppointmentCreate, request: Request):
    await get_current_user(request)
    
    apt_id = f"apt_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    apt_doc = {
        "appointment_id": apt_id,
        "lead_id": apt_data.lead_id,
        "agent_id": apt_data.agent_id,
        "title": apt_data.title,
        "description": apt_data.description,
        "scheduled_at": apt_data.scheduled_at.isoformat(),
        "status": "pendiente",
        "created_at": now
    }
    
    await db.appointments.insert_one(apt_doc)
    
    # Update lead status
    await db.leads.update_one(
        {"lead_id": apt_data.lead_id},
        {"$set": {"status": "cita_agendada", "updated_at": now}}
    )
    
    # Get names
    lead = await db.leads.find_one({"lead_id": apt_data.lead_id}, {"_id": 0})
    agent = await db.users.find_one({"user_id": apt_data.agent_id}, {"_id": 0})
    
    return AppointmentResponse(
        appointment_id=apt_id,
        lead_id=apt_data.lead_id,
        lead_name=lead["full_name"] if lead else None,
        agent_id=apt_data.agent_id,
        agent_name=agent["name"] if agent else None,
        title=apt_data.title,
        description=apt_data.description,
        scheduled_at=apt_data.scheduled_at,
        status="pendiente",
        created_at=datetime.fromisoformat(now)
    )

@api_router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(
    request: Request,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    current_user = await get_current_user(request)
    
    query = {}
    
    if current_user["role"] == "agente":
        query["agent_id"] = current_user["user_id"]
    elif agent_id:
        query["agent_id"] = agent_id
    
    if status:
        query["status"] = status
    
    if date_from:
        query["scheduled_at"] = {"$gte": date_from}
    if date_to:
        if "scheduled_at" in query:
            query["scheduled_at"]["$lte"] = date_to
        else:
            query["scheduled_at"] = {"$lte": date_to}
    
    appointments = await db.appointments.find(query, {"_id": 0}).sort("scheduled_at", 1).to_list(1000)
    
    # Get all lead and agent info
    lead_ids = list(set([a["lead_id"] for a in appointments]))
    agent_ids = list(set([a["agent_id"] for a in appointments]))
    
    leads = await db.leads.find({"lead_id": {"$in": lead_ids}}, {"_id": 0}).to_list(1000)
    agents = await db.users.find({"user_id": {"$in": agent_ids}}, {"_id": 0}).to_list(1000)
    
    lead_map = {l["lead_id"]: l["full_name"] for l in leads}
    agent_map = {a["user_id"]: a["name"] for a in agents}
    
    result = []
    for apt in appointments:
        scheduled_at = apt.get("scheduled_at")
        created_at = apt.get("created_at")
        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at)
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        result.append(AppointmentResponse(
            appointment_id=apt["appointment_id"],
            lead_id=apt["lead_id"],
            lead_name=lead_map.get(apt["lead_id"]),
            agent_id=apt["agent_id"],
            agent_name=agent_map.get(apt["agent_id"]),
            title=apt["title"],
            description=apt.get("description"),
            scheduled_at=scheduled_at,
            status=apt["status"],
            created_at=created_at
        ))
    
    return result

@api_router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(appointment_id: str, update_data: AppointmentUpdate, request: Request):
    await get_current_user(request)
    
    update_dict = {}
    if update_data.title:
        update_dict["title"] = update_data.title
    if update_data.description is not None:
        update_dict["description"] = update_data.description
    if update_data.scheduled_at:
        update_dict["scheduled_at"] = update_data.scheduled_at.isoformat()
    if update_data.status:
        update_dict["status"] = update_data.status
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.appointments.update_one(
        {"appointment_id": appointment_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    apt = await db.appointments.find_one({"appointment_id": appointment_id}, {"_id": 0})
    
    lead = await db.leads.find_one({"lead_id": apt["lead_id"]}, {"_id": 0})
    agent = await db.users.find_one({"user_id": apt["agent_id"]}, {"_id": 0})
    
    scheduled_at = apt.get("scheduled_at")
    created_at = apt.get("created_at")
    if isinstance(scheduled_at, str):
        scheduled_at = datetime.fromisoformat(scheduled_at)
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return AppointmentResponse(
        appointment_id=apt["appointment_id"],
        lead_id=apt["lead_id"],
        lead_name=lead["full_name"] if lead else None,
        agent_id=apt["agent_id"],
        agent_name=agent["name"] if agent else None,
        title=apt["title"],
        description=apt.get("description"),
        scheduled_at=scheduled_at,
        status=apt["status"],
        created_at=created_at
    )

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, request: Request):
    await require_roles(["admin", "gerente", "supervisor"])(request)
    
    result = await db.appointments.delete_one({"appointment_id": appointment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    return {"message": "Cita eliminada"}

# ============== WEBHOOK ENDPOINTS (for N8N) ==============

@api_router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(webhook_data: WebhookCreate, request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
    secret_key = f"whsec_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc).isoformat()
    
    webhook_doc = {
        "webhook_id": webhook_id,
        "name": webhook_data.name,
        "url": webhook_data.url,
        "events": webhook_data.events,
        "is_active": webhook_data.is_active,
        "secret_key": secret_key,
        "created_at": now
    }
    
    await db.webhooks.insert_one(webhook_doc)
    
    return WebhookResponse(
        webhook_id=webhook_id,
        name=webhook_data.name,
        url=webhook_data.url,
        events=webhook_data.events,
        is_active=webhook_data.is_active,
        secret_key=secret_key,
        created_at=datetime.fromisoformat(now)
    )

@api_router.get("/webhooks", response_model=List[WebhookResponse])
async def get_webhooks(request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    webhooks = await db.webhooks.find({}, {"_id": 0}).to_list(100)
    
    result = []
    for wh in webhooks:
        created_at = wh.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        result.append(WebhookResponse(
            webhook_id=wh["webhook_id"],
            name=wh["name"],
            url=wh["url"],
            events=wh["events"],
            is_active=wh["is_active"],
            secret_key=wh["secret_key"],
            created_at=created_at
        ))
    
    return result

@api_router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    result = await db.webhooks.delete_one({"webhook_id": webhook_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webhook no encontrado")
    
    return {"message": "Webhook eliminado"}

# N8N incoming webhook - receives leads from external sources
@api_router.post("/webhooks/incoming/lead")
async def incoming_lead_webhook(payload: N8NLeadPayload):
    """
    Endpoint for N8N to send leads from WhatsApp, Facebook, Instagram, TikTok
    """
    lead_id = f"lead_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    # Find agent based on career
    assigned_agent_id = None
    agent_data = None
    career_agent = await find_agent_for_career(payload.career_interest)
    if career_agent:
        assigned_agent_id = career_agent["user_id"]
        agent_data = {"name": career_agent["name"], "email": career_agent.get("email"), "phone": career_agent.get("phone")}
    
    lead_doc = {
        "lead_id": lead_id,
        "full_name": payload.full_name,
        "email": payload.email,
        "phone": payload.phone,
        "career_interest": payload.career_interest,
        "source": payload.source,
        "source_detail": payload.source_detail,
        "whatsapp_number": payload.whatsapp_number,
        "status": "nuevo",
        "assigned_agent_id": assigned_agent_id,
        "notes": None,
        "created_at": now,
        "updated_at": now,
        "created_by": "webhook"
    }
    
    await db.leads.insert_one(lead_doc)
    
    # Trigger outgoing webhooks
    await trigger_webhooks("lead.created", lead_doc)
    
    # Send notification for new lead from webhook
    await send_notification("lead.created", {
        "lead_id": lead_id,
        "full_name": payload.full_name,
        "email": payload.email,
        "phone": payload.phone,
        "career_interest": payload.career_interest,
        "source": payload.source,
        "source_detail": payload.source_detail
    }, agent_data)
    
    return {"success": True, "lead_id": lead_id, "assigned_agent_id": assigned_agent_id}

async def trigger_webhooks(event: str, data: dict):
    """Trigger all active webhooks for a given event"""
    webhooks = await db.webhooks.find(
        {"is_active": True, "events": event},
        {"_id": 0}
    ).to_list(100)
    
    async with httpx.AsyncClient() as client:
        for wh in webhooks:
            try:
                await client.post(
                    wh["url"],
                    json={
                        "event": event,
                        "data": data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    headers={
                        "X-Webhook-Secret": wh["secret_key"],
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Failed to trigger webhook {wh['webhook_id']}: {e}")

async def send_notification(event_type: str, lead_data: dict, agent_data: dict = None):
    """Send notification to configured phone number via webhook"""
    settings = await db.notification_settings.find_one({}, {"_id": 0})
    
    if not settings:
        return
    
    # Check if notifications are enabled for this event
    if event_type == "lead.created" and not settings.get("notify_on_new_lead", True):
        return
    if event_type == "appointment.created" and not settings.get("notify_on_appointment", True):
        return
    
    notification_phone = settings.get("notification_phone")
    webhook_url = settings.get("notification_webhook_url")
    
    if not notification_phone and not webhook_url:
        return
    
    # Build notification message
    if event_type == "lead.created":
        message = f"🔔 *Nuevo Lead*\n\n"
        message += f"👤 *Nombre:* {lead_data.get('full_name')}\n"
        message += f"📧 *Email:* {lead_data.get('email')}\n"
        message += f"📱 *Teléfono:* {lead_data.get('phone')}\n"
        message += f"🎓 *Carrera:* {lead_data.get('career_interest')}\n"
        message += f"📍 *Fuente:* {lead_data.get('source')}\n"
        if agent_data:
            message += f"👨‍💼 *Agente asignado:* {agent_data.get('name')}\n"
        message += f"\n⏰ {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} UTC"
    elif event_type == "appointment.created":
        message = f"📅 *Nueva Cita Agendada*\n\n"
        message += f"👤 *Lead:* {lead_data.get('full_name')}\n"
        message += f"📱 *Teléfono:* {lead_data.get('phone')}\n"
        message += f"📋 *Título:* {lead_data.get('title')}\n"
        message += f"🕐 *Fecha:* {lead_data.get('scheduled_at')}\n"
        if agent_data:
            message += f"👨‍💼 *Agente:* {agent_data.get('name')}\n"
    else:
        message = f"🔔 Notificación: {event_type}"
    
    notification_payload = {
        "event": event_type,
        "phone": notification_phone,
        "message": message,
        "lead": lead_data,
        "agent": agent_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Send via Twilio WhatsApp if configured
    if notification_phone and twilio_client:
        try:
            await send_whatsapp_message(notification_phone, message)
            logger.info(f"WhatsApp notification sent for {event_type}")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp notification: {e}")
    
    # Send to configured webhook (N8N) as backup
    if webhook_url:
        async with httpx.AsyncClient() as http_client:
            try:
                await http_client.post(
                    webhook_url,
                    json=notification_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                logger.info(f"Webhook notification sent for {event_type}")
            except Exception as e:
                logger.error(f"Failed to send webhook notification: {e}")

async def send_whatsapp_message(to_number: str, message: str) -> dict:
    """Send WhatsApp message using Twilio"""
    if not twilio_client:
        logger.warning("Twilio client not initialized")
        return {"success": False, "error": "Twilio not configured"}
    
    try:
        # Format phone number
        if not to_number.startswith('+'):
            to_number = '+' + to_number
        
        # Send via Twilio
        twilio_message = twilio_client.messages.create(
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            body=message,
            to=f"whatsapp:{to_number}"
        )
        
        logger.info(f"WhatsApp message sent. SID: {twilio_message.sid}")
        return {
            "success": True,
            "message_sid": twilio_message.sid,
            "status": twilio_message.status
        }
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return {"success": False, "error": str(e)}

# ============== NOTIFICATION SETTINGS ENDPOINTS ==============

@api_router.get("/settings/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    settings = await db.notification_settings.find_one({}, {"_id": 0})
    
    if not settings:
        # Create default settings
        settings_id = f"settings_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        settings = {
            "settings_id": settings_id,
            "notification_phone": None,
            "notification_webhook_url": None,
            "notify_on_new_lead": True,
            "notify_on_appointment": True,
            "notify_supervisors": False,
            "updated_at": now
        }
        await db.notification_settings.insert_one(settings)
    
    updated_at = settings.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    return NotificationSettingsResponse(
        settings_id=settings["settings_id"],
        notification_phone=settings.get("notification_phone"),
        notification_webhook_url=settings.get("notification_webhook_url"),
        notify_on_new_lead=settings.get("notify_on_new_lead", True),
        notify_on_appointment=settings.get("notify_on_appointment", True),
        notify_supervisors=settings.get("notify_supervisors", False),
        updated_at=updated_at
    )

@api_router.put("/settings/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(update_data: NotificationSettingsUpdate, request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    now = datetime.now(timezone.utc).isoformat()
    update_dict = update_data.model_dump()
    update_dict["updated_at"] = now
    
    # Check if settings exist
    existing = await db.notification_settings.find_one({}, {"_id": 0})
    
    if existing:
        await db.notification_settings.update_one(
            {"settings_id": existing["settings_id"]},
            {"$set": update_dict}
        )
        settings_id = existing["settings_id"]
    else:
        settings_id = f"settings_{uuid.uuid4().hex[:12]}"
        update_dict["settings_id"] = settings_id
        await db.notification_settings.insert_one(update_dict)
    
    return NotificationSettingsResponse(
        settings_id=settings_id,
        notification_phone=update_dict.get("notification_phone"),
        notification_webhook_url=update_dict.get("notification_webhook_url"),
        notify_on_new_lead=update_dict.get("notify_on_new_lead", True),
        notify_on_appointment=update_dict.get("notify_on_appointment", True),
        notify_supervisors=update_dict.get("notify_supervisors", False),
        updated_at=datetime.fromisoformat(now)
    )

@api_router.post("/settings/notifications/test")
async def test_notification(request: Request):
    """Send a test notification to verify configuration"""
    await require_roles(["admin", "gerente"])(request)
    
    test_lead = {
        "full_name": "Lead de Prueba",
        "email": "test@ejemplo.com",
        "phone": "+521234567890",
        "career_interest": "Ingeniería",
        "source": "manual"
    }
    
    test_agent = {
        "name": "Admin Demo"
    }
    
    await send_notification("lead.created", test_lead, test_agent)
    
    return {"message": "Notificación de prueba enviada"}

# ============== WHATSAPP ENDPOINTS ==============

@api_router.post("/whatsapp/send")
async def send_whatsapp(request: Request, to_number: str, message: str):
    """Send a WhatsApp message directly"""
    await require_roles(["admin", "gerente"])(request)
    
    result = await send_whatsapp_message(to_number, message)
    
    if result["success"]:
        return {"success": True, "message_sid": result.get("message_sid")}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send message"))

@api_router.get("/whatsapp/status")
async def get_whatsapp_status(request: Request):
    """Check WhatsApp integration status"""
    await require_roles(["admin", "gerente"])(request)
    
    return {
        "configured": twilio_client is not None,
        "account_sid": TWILIO_ACCOUNT_SID[:10] + "..." if TWILIO_ACCOUNT_SID else None,
        "whatsapp_number": TWILIO_WHATSAPP_NUMBER
    }

# ============== GOOGLE CALENDAR ENDPOINTS ==============

def get_frontend_url():
    """Get frontend URL for redirects"""
    return os.environ.get('FRONTEND_URL', 'https://leadsync-16.preview.emergentagent.com')

def get_google_redirect_uri():
    """Get Google OAuth redirect URI"""
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://leadsync-16.preview.emergentagent.com')
    return f"{backend_url}/api/auth/google/calendar/callback"

@api_router.get("/auth/google/calendar/login")
async def google_calendar_login(request: Request):
    """Initiate Google Calendar OAuth flow"""
    current_user = await get_current_user(request)
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google Calendar no está configurado")
    
    # Build authorization URL
    auth_url = "https://accounts.google.com/o/oauth2/auth"
    redirect_uri = get_google_redirect_uri()
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_CALENDAR_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": current_user["user_id"]  # Pass user_id in state
    }
    
    url = f"{auth_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    return {"authorization_url": url}

@api_router.get("/auth/google/calendar/callback")
async def google_calendar_callback(code: str, state: str):
    """Handle Google Calendar OAuth callback"""
    try:
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        redirect_uri = get_google_redirect_uri()
        
        async with httpx.AsyncClient() as http_client:
            token_response = await http_client.post(token_url, data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            })
            
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                return RedirectResponse(f"{get_frontend_url()}/calendar?error=token_exchange_failed")
            
            tokens = token_response.json()
            
            # Get user email from Google
            userinfo_response = await http_client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            
            if userinfo_response.status_code != 200:
                return RedirectResponse(f"{get_frontend_url()}/calendar?error=userinfo_failed")
            
            google_user = userinfo_response.json()
        
        # Save tokens to user document
        user_id = state  # User ID passed in state parameter
        
        await db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "google_calendar_tokens": {
                        "access_token": tokens["access_token"],
                        "refresh_token": tokens.get("refresh_token"),
                        "token_type": tokens.get("token_type"),
                        "expires_in": tokens.get("expires_in"),
                        "obtained_at": datetime.now(timezone.utc).isoformat()
                    },
                    "google_calendar_email": google_user.get("email"),
                    "google_calendar_connected": True
                }
            }
        )
        
        logger.info(f"Google Calendar connected for user {user_id}")
        return RedirectResponse(f"{get_frontend_url()}/calendar?google_connected=true")
        
    except Exception as e:
        logger.error(f"Google Calendar callback error: {e}")
        return RedirectResponse(f"{get_frontend_url()}/calendar?error=callback_failed")

async def get_google_credentials(user_id: str):
    """Get valid Google credentials for a user, refreshing if needed"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    
    if not user or not user.get("google_calendar_tokens"):
        return None
    
    tokens = user["google_calendar_tokens"]
    
    creds = Credentials(
        token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    
    # Check if token needs refresh
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            
            # Save new access token
            await db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "google_calendar_tokens.access_token": creds.token,
                        "google_calendar_tokens.obtained_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to refresh Google token: {e}")
            return None
    
    return creds

@api_router.get("/calendar/google/status")
async def get_google_calendar_status(request: Request):
    """Check if user has connected Google Calendar"""
    current_user = await get_current_user(request)
    
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    
    return {
        "connected": user.get("google_calendar_connected", False),
        "email": user.get("google_calendar_email"),
        "configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    }

@api_router.post("/calendar/google/disconnect")
async def disconnect_google_calendar(request: Request):
    """Disconnect Google Calendar"""
    current_user = await get_current_user(request)
    
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$unset": {
                "google_calendar_tokens": "",
                "google_calendar_email": ""
            },
            "$set": {
                "google_calendar_connected": False
            }
        }
    )
    
    return {"message": "Google Calendar desconectado"}

@api_router.get("/calendar/google/events")
async def get_google_calendar_events(request: Request, max_results: int = 50):
    """Get upcoming events from Google Calendar"""
    current_user = await get_current_user(request)
    
    creds = await get_google_credentials(current_user["user_id"])
    if not creds:
        raise HTTPException(status_code=400, detail="Google Calendar no conectado")
    
    try:
        service = build("calendar", "v3", credentials=creds)
        
        now = datetime.now(timezone.utc).isoformat()
        
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = events_result.get("items", [])
        
        return {"events": events}
    
    except Exception as e:
        logger.error(f"Error fetching Google Calendar events: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener eventos")

@api_router.post("/calendar/google/sync-appointment/{appointment_id}")
async def sync_appointment_to_google(appointment_id: str, request: Request):
    """Sync an appointment to Google Calendar"""
    current_user = await get_current_user(request)
    
    # Get appointment
    appointment = await db.appointments.find_one({"appointment_id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Get Google credentials for the agent
    agent_id = appointment["agent_id"]
    creds = await get_google_credentials(agent_id)
    
    if not creds:
        raise HTTPException(status_code=400, detail="El agente no tiene Google Calendar conectado")
    
    # Get lead info
    lead = await db.leads.find_one({"lead_id": appointment["lead_id"]}, {"_id": 0})
    
    try:
        service = build("calendar", "v3", credentials=creds)
        
        # Parse scheduled time
        scheduled_at = appointment["scheduled_at"]
        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
        
        # Create event
        event = {
            "summary": appointment["title"],
            "description": f"""Cita con lead: {lead['full_name'] if lead else 'Desconocido'}
            
Teléfono: {lead['phone'] if lead else 'N/A'}
Email: {lead['email'] if lead else 'N/A'}
Carrera de interés: {lead['career_interest'] if lead else 'N/A'}

Notas: {appointment.get('description', '')}""",
            "start": {
                "dateTime": scheduled_at.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": (scheduled_at + timedelta(hours=1)).isoformat(),
                "timeZone": "UTC"
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                    {"method": "popup", "minutes": 10}
                ]
            }
        }
        
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        
        # Save Google Calendar event ID
        await db.appointments.update_one(
            {"appointment_id": appointment_id},
            {
                "$set": {
                    "google_calendar_event_id": created_event["id"],
                    "google_calendar_synced": True,
                    "google_calendar_link": created_event.get("htmlLink")
                }
            }
        )
        
        logger.info(f"Appointment {appointment_id} synced to Google Calendar")
        
        return {
            "success": True,
            "event_id": created_event["id"],
            "event_link": created_event.get("htmlLink")
        }
    
    except Exception as e:
        logger.error(f"Error syncing to Google Calendar: {e}")
        raise HTTPException(status_code=500, detail=f"Error al sincronizar: {str(e)}")

@api_router.delete("/calendar/google/event/{event_id}")
async def delete_google_calendar_event(event_id: str, request: Request):
    """Delete an event from Google Calendar"""
    current_user = await get_current_user(request)
    
    creds = await get_google_credentials(current_user["user_id"])
    if not creds:
        raise HTTPException(status_code=400, detail="Google Calendar no conectado")
    
    try:
        service = build("calendar", "v3", credentials=creds)
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        
        # Update any appointment that had this event
        await db.appointments.update_many(
            {"google_calendar_event_id": event_id},
            {
                "$set": {
                    "google_calendar_synced": False
                },
                "$unset": {
                    "google_calendar_event_id": "",
                    "google_calendar_link": ""
                }
            }
        )
        
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Error deleting Google Calendar event: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar evento")

# ============== DASHBOARD ENDPOINTS ==============

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(request: Request):
    current_user = await get_current_user(request)
    
    # Base query based on role
    base_query = {}
    if current_user["role"] == "agente":
        base_query["assigned_agent_id"] = current_user["user_id"]
    
    # Total leads
    total_leads = await db.leads.count_documents(base_query)
    
    # Leads by status
    status_pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_result = await db.leads.aggregate(status_pipeline).to_list(100)
    leads_by_status = {s["_id"]: s["count"] for s in status_result}
    
    # Leads by source
    source_pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]
    source_result = await db.leads.aggregate(source_pipeline).to_list(100)
    leads_by_source = {s["_id"]: s["count"] for s in source_result}
    
    # Leads by career
    career_pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$career_interest", "count": {"$sum": 1}}}
    ]
    career_result = await db.leads.aggregate(career_pipeline).to_list(100)
    leads_by_career = {c["_id"]: c["count"] for c in career_result}
    
    # Leads by agent (only for admin/gerente/supervisor)
    leads_by_agent = {}
    if current_user["role"] in ["admin", "gerente", "supervisor"]:
        agent_pipeline = [
            {"$match": base_query},
            {"$group": {"_id": "$assigned_agent_id", "count": {"$sum": 1}}}
        ]
        agent_result = await db.leads.aggregate(agent_pipeline).to_list(100)
        
        # Get agent names
        agent_ids = [a["_id"] for a in agent_result if a["_id"]]
        agents = await db.users.find({"user_id": {"$in": agent_ids}}, {"_id": 0}).to_list(100)
        agent_name_map = {a["user_id"]: a["name"] for a in agents}
        
        leads_by_agent = {
            agent_name_map.get(a["_id"], "Sin asignar"): a["count"]
            for a in agent_result
        }
    
    # Conversion rate
    converted = leads_by_status.get("convertido", 0)
    conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
    
    # New leads today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_query = {**base_query, "created_at": {"$gte": today_start.isoformat()}}
    new_leads_today = await db.leads.count_documents(today_query)
    
    # Appointments today
    apt_query = {}
    if current_user["role"] == "agente":
        apt_query["agent_id"] = current_user["user_id"]
    apt_query["scheduled_at"] = {
        "$gte": today_start.isoformat(),
        "$lt": (today_start + timedelta(days=1)).isoformat()
    }
    appointments_today = await db.appointments.count_documents(apt_query)
    
    return DashboardStats(
        total_leads=total_leads,
        leads_by_status=leads_by_status,
        leads_by_source=leads_by_source,
        leads_by_career=leads_by_career,
        leads_by_agent=leads_by_agent,
        conversion_rate=round(conversion_rate, 2),
        new_leads_today=new_leads_today,
        appointments_today=appointments_today
    )

@api_router.get("/dashboard/recent-leads", response_model=List[LeadResponse])
async def get_recent_leads(request: Request, limit: int = 10):
    current_user = await get_current_user(request)
    
    query = {}
    if current_user["role"] == "agente":
        query["assigned_agent_id"] = current_user["user_id"]
    
    leads = await db.leads.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    agent_ids = list(set([l.get("assigned_agent_id") for l in leads if l.get("assigned_agent_id")]))
    agents = await db.users.find({"user_id": {"$in": agent_ids}}, {"_id": 0}).to_list(100)
    agent_map = {a["user_id"]: a["name"] for a in agents}
    
    result = []
    for lead in leads:
        created_at = lead.get("created_at")
        updated_at = lead.get("updated_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        result.append(LeadResponse(
            lead_id=lead["lead_id"],
            full_name=lead["full_name"],
            email=lead["email"],
            phone=lead["phone"],
            career_interest=lead["career_interest"],
            source=lead["source"],
            source_detail=lead.get("source_detail"),
            status=lead["status"],
            assigned_agent_id=lead.get("assigned_agent_id"),
            assigned_agent_name=agent_map.get(lead.get("assigned_agent_id")),
            notes=lead.get("notes"),
            created_at=created_at,
            updated_at=updated_at
        ))
    
    return result

# ============== CONSTANTS ENDPOINTS ==============

@api_router.get("/constants/careers")
async def get_careers():
    """Get all careers (from database, initializing with defaults if needed)"""
    careers_doc = await db.settings.find_one({"type": "careers"}, {"_id": 0})
    if careers_doc and "items" in careers_doc:
        return {"careers": careers_doc["items"]}
    
    # Initialize with default careers if not exists
    await db.settings.update_one(
        {"type": "careers"},
        {"$set": {"items": list(DEFAULT_CAREERS), "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"careers": list(DEFAULT_CAREERS)}

@api_router.post("/careers")
async def add_career(request: Request):
    """Add a new career"""
    await require_roles(["admin", "gerente"])(request)
    body = await request.json()
    career_name = body.get("name", "").strip()
    
    if not career_name:
        raise HTTPException(status_code=400, detail="Nombre de carrera requerido")
    
    # Get current careers (ensure initialized)
    careers_doc = await db.settings.find_one({"type": "careers"}, {"_id": 0})
    if not careers_doc or "items" not in careers_doc:
        current_careers = list(DEFAULT_CAREERS)
        await db.settings.update_one(
            {"type": "careers"},
            {"$set": {"items": current_careers, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
    else:
        current_careers = careers_doc["items"]
    
    if career_name in current_careers:
        raise HTTPException(status_code=400, detail="La carrera ya existe")
    
    current_careers.append(career_name)
    
    await db.settings.update_one(
        {"type": "careers"},
        {"$set": {"items": current_careers, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    logger.info(f"Career added: {career_name}")
    return {"careers": current_careers, "message": "Carrera agregada"}

@api_router.delete("/careers/{career_name}")
async def delete_career(career_name: str, request: Request):
    """Delete a career"""
    await require_roles(["admin", "gerente"])(request)
    
    # Get current careers (ensure initialized)
    careers_doc = await db.settings.find_one({"type": "careers"}, {"_id": 0})
    if not careers_doc or "items" not in careers_doc:
        current_careers = list(DEFAULT_CAREERS)
        await db.settings.update_one(
            {"type": "careers"},
            {"$set": {"items": current_careers, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
    else:
        current_careers = careers_doc["items"]
    
    if career_name not in current_careers:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    
    current_careers.remove(career_name)
    
    await db.settings.update_one(
        {"type": "careers"},
        {"$set": {"items": current_careers, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Also remove from users' assigned_careers
    await db.users.update_many(
        {"assigned_careers": career_name},
        {"$pull": {"assigned_careers": career_name}}
    )
    
    logger.info(f"Career deleted: {career_name}")
    return {"careers": current_careers, "message": "Carrera eliminada"}

@api_router.get("/constants/sources")
async def get_sources():
    return {"sources": LEAD_SOURCES}

@api_router.get("/constants/statuses")
async def get_statuses():
    return {"statuses": LEAD_STATUSES}

@api_router.get("/constants/roles")
async def get_roles():
    return {"roles": USER_ROLES}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
