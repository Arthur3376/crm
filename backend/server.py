from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'leadflow-pro-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="LeadFlow Pro API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== ENUMS & CONSTANTS ==============
USER_ROLES = ["admin", "gerente", "supervisor", "agente"]
LEAD_SOURCES = ["facebook", "instagram", "tiktok", "manual", "webhook"]
LEAD_STATUSES = ["nuevo", "contactado", "en_progreso", "cita_agendada", "convertido", "no_interesado"]
CAREERS = ["Ingeniería", "Medicina", "Derecho", "Administración", "Contabilidad", "Psicología", "Diseño", "Marketing", "Otra"]
NOTIFICATION_EVENTS = ["lead.created", "lead.updated", "appointment.created", "appointment.reminder"]

# ============== PYDANTIC MODELS ==============

# User Models
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "agente"
    phone: Optional[str] = None
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "agente"
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    is_active: bool = True
    picture: Optional[str] = None
    created_at: datetime

class TokenResponse(BaseModel):
    token: str
    user: UserResponse

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
        created_at=created_at
    )
    
    return TokenResponse(token=token, user=user_response)

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
        created_at=created_at
    )

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    await require_roles(["admin"])(request)
    
    result = await db.users.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Usuario eliminado"}

# ============== LEAD ENDPOINTS ==============

@api_router.post("/leads", response_model=LeadResponse)
async def create_lead(lead_data: LeadCreate, request: Request):
    current_user = await get_current_user(request)
    
    lead_id = f"lead_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    lead_doc = {
        "lead_id": lead_id,
        "full_name": lead_data.full_name,
        "email": lead_data.email,
        "phone": lead_data.phone,
        "career_interest": lead_data.career_interest,
        "source": lead_data.source,
        "source_detail": lead_data.source_detail,
        "status": "nuevo",
        "assigned_agent_id": lead_data.assigned_agent_id or current_user["user_id"],
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
        "assigned_agent_id": None,
        "notes": None,
        "created_at": now,
        "updated_at": now,
        "created_by": "webhook"
    }
    
    await db.leads.insert_one(lead_doc)
    
    # Trigger outgoing webhooks
    await trigger_webhooks("lead.created", lead_doc)
    
    return {"success": True, "lead_id": lead_id}

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
    
    # Send to configured webhook (N8N)
    if webhook_url:
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    webhook_url,
                    json=notification_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                logger.info(f"Notification sent for {event_type}")
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

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
    return {"careers": CAREERS}

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
