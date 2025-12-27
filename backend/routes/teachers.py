"""Teacher management routes"""
import uuid
from fastapi import APIRouter, HTTPException, Request
from typing import List
from datetime import datetime, timezone

from config import db, logger
from models.teachers import TeacherCreate, TeacherUpdate, TeacherResponse
from utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.post("", response_model=TeacherResponse)
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
    return TeacherResponse(**teacher)


@router.get("", response_model=List[TeacherResponse])
async def get_teachers(request: Request):
    """Get all teachers"""
    await get_current_user(request)
    
    teachers = await db.teachers.find({}, {"_id": 0}).to_list(1000)
    return [TeacherResponse(**t) for t in teachers]


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(teacher_id: str, request: Request):
    """Get a single teacher"""
    await get_current_user(request)
    
    teacher = await db.teachers.find_one({"teacher_id": teacher_id}, {"_id": 0})
    if not teacher:
        raise HTTPException(status_code=404, detail="Maestro no encontrado")
    
    return TeacherResponse(**teacher)


@router.put("/{teacher_id}", response_model=TeacherResponse)
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
    return TeacherResponse(**updated_teacher)


@router.delete("/{teacher_id}")
async def delete_teacher(teacher_id: str, request: Request):
    """Delete a teacher"""
    await require_roles(["admin"])(request)
    
    result = await db.teachers.delete_one({"teacher_id": teacher_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Maestro no encontrado")
    
    return {"message": "Maestro eliminado"}
