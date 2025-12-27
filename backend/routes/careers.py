"""Career management routes"""
import uuid
from fastapi import APIRouter, HTTPException, Request
from typing import List
from datetime import datetime, timezone

from config import db, logger
from models.careers import CareerCreate, CareerUpdate, CareerResponse
from utils.auth import get_current_user, require_roles

router = APIRouter(prefix="/careers", tags=["careers"])


@router.post("/full", response_model=CareerResponse)
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
    return CareerResponse(**career)


@router.get("/full", response_model=List[CareerResponse])
async def get_careers_full(request: Request):
    """Get all careers with schedules"""
    await get_current_user(request)
    
    careers = await db.careers_full.find({}, {"_id": 0}).to_list(1000)
    return [CareerResponse(**c) for c in careers]


@router.get("/full/{career_id}", response_model=CareerResponse)
async def get_career_full(career_id: str, request: Request):
    """Get a single career with schedules"""
    await get_current_user(request)
    
    career = await db.careers_full.find_one({"career_id": career_id}, {"_id": 0})
    if not career:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    
    return CareerResponse(**career)


@router.put("/full/{career_id}", response_model=CareerResponse)
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
    return CareerResponse(**updated_career)


@router.delete("/full/{career_id}")
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
    
    await db.careers_full.delete_one({"career_id": career_id})
    
    return {"message": "Carrera eliminada"}


@router.get("/list")
async def get_careers_list(request: Request):
    """Get simple list of career names (for dropdowns)"""
    await get_current_user(request)
    
    # Get from careers_full collection
    careers = await db.careers_full.find({"is_active": True}, {"_id": 0, "name": 1}).to_list(1000)
    career_names = [c["name"] for c in careers]
    
    # Also check settings for any additional careers
    settings = await db.settings.find_one({"type": "careers"}, {"_id": 0})
    if settings:
        for name in settings.get("items", []):
            if name not in career_names:
                career_names.append(name)
    
    return {"careers": career_names}
