"""Authentication routes"""
import uuid
import asyncio
import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
import os

import sys; sys.path.insert(0, "/app/backend"); from config import db, logger, RESEND_API_KEY, SENDER_EMAIL
from models.users import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from utils.auth import hash_password, verify_password, create_jwt_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
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


@router.post("/login", response_model=TokenResponse)
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


@router.post("/forgot-password")
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
        import resend
        frontend_url = os.environ.get('FRONTEND_URL', 'https://campus-flow-8.preview.emergentagent.com')
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


@router.post("/reset-password")
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


@router.post("/session")
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


@router.get("/me", response_model=UserResponse)
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
        assigned_careers=user.get("assigned_careers", []),
        created_at=created_at
    )


@router.post("/logout")
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
