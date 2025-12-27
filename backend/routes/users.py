"""User management routes"""
import uuid
from fastapi import APIRouter, HTTPException, Request
from typing import List
from datetime import datetime, timezone

import sys; sys.path.insert(0, "/app/backend"); from config import db, logger
from models.users import UserCreate, UserUpdate, UserResponse, AdminResetPasswordRequest
from utils.auth import hash_password, get_current_user, require_roles

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
async def get_users(request: Request):
    await require_roles(["admin", "gerente"])(request)
    
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


@router.get("/agents", response_model=List[UserResponse])
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


@router.get("/{user_id}", response_model=UserResponse)
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


@router.post("", response_model=UserResponse)
async def create_user(user_data: UserCreate, request: Request):
    await require_roles(["admin"])(request)
    
    # Check if email already exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
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
        "created_at": now
    }
    
    await db.users.insert_one(user_doc)
    
    return UserResponse(
        user_id=user_id,
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        phone=user_data.phone,
        is_active=True,
        picture=None,
        assigned_careers=user_data.assigned_careers,
        created_at=datetime.fromisoformat(now)
    )


@router.put("/{user_id}", response_model=UserResponse)
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


@router.delete("/{user_id}")
async def delete_user(user_id: str, request: Request):
    await require_roles(["admin"])(request)
    
    result = await db.users.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Usuario eliminado"}


@router.post("/{user_id}/reset-password")
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
