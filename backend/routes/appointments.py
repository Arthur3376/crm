"""Appointment management routes"""
import uuid
from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from datetime import datetime, timezone

from config import db, logger
from models.appointments import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from utils.auth import get_current_user, require_roles
from utils.helpers import send_notification

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse)
async def create_appointment(appointment_data: AppointmentCreate, request: Request):
    current_user = await get_current_user(request)
    
    appointment_id = f"apt_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Get lead and agent names
    lead = await db.leads.find_one({"lead_id": appointment_data.lead_id}, {"_id": 0})
    agent = await db.users.find_one({"user_id": appointment_data.agent_id}, {"_id": 0})
    
    appointment = {
        "appointment_id": appointment_id,
        "lead_id": appointment_data.lead_id,
        "lead_name": lead["full_name"] if lead else None,
        "agent_id": appointment_data.agent_id,
        "agent_name": agent["name"] if agent else None,
        "title": appointment_data.title,
        "description": appointment_data.description,
        "scheduled_at": appointment_data.scheduled_at.isoformat(),
        "status": "scheduled",
        "created_at": now.isoformat(),
        "created_by": current_user["user_id"]
    }
    
    await db.appointments.insert_one(appointment)
    appointment.pop("_id", None)
    
    # Send notification
    await send_notification("appointment.created", {
        "appointment_id": appointment_id,
        "title": appointment_data.title,
        "scheduled_at": appointment_data.scheduled_at.isoformat(),
        "lead_name": lead["full_name"] if lead else None
    })
    
    return AppointmentResponse(
        appointment_id=appointment_id,
        lead_id=appointment_data.lead_id,
        lead_name=lead["full_name"] if lead else None,
        agent_id=appointment_data.agent_id,
        agent_name=agent["name"] if agent else None,
        title=appointment_data.title,
        description=appointment_data.description,
        scheduled_at=appointment_data.scheduled_at,
        status="scheduled",
        created_at=now
    )


@router.get("", response_model=List[AppointmentResponse])
async def get_appointments(
    request: Request,
    agent_id: Optional[str] = None,
    status: Optional[str] = None
):
    current_user = await get_current_user(request)
    
    query = {}
    
    # Role-based filtering
    if current_user["role"] == "agente":
        query["agent_id"] = current_user["user_id"]
    elif agent_id:
        query["agent_id"] = agent_id
    
    if status:
        query["status"] = status
    
    appointments = await db.appointments.find(query, {"_id": 0}).sort("scheduled_at", 1).to_list(1000)
    
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
            lead_name=apt.get("lead_name"),
            agent_id=apt["agent_id"],
            agent_name=apt.get("agent_name"),
            title=apt["title"],
            description=apt.get("description"),
            scheduled_at=scheduled_at,
            status=apt["status"],
            created_at=created_at
        ))
    
    return result


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(appointment_id: str, update_data: AppointmentUpdate, request: Request):
    await get_current_user(request)
    
    appointment = await db.appointments.find_one({"appointment_id": appointment_id}, {"_id": 0})
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    update_dict = {}
    for k, v in update_data.model_dump().items():
        if v is not None:
            if k == "scheduled_at":
                update_dict[k] = v.isoformat()
            else:
                update_dict[k] = v
    
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.appointments.update_one({"appointment_id": appointment_id}, {"$set": update_dict})
    
    appointment = await db.appointments.find_one({"appointment_id": appointment_id}, {"_id": 0})
    
    scheduled_at = appointment.get("scheduled_at")
    created_at = appointment.get("created_at")
    if isinstance(scheduled_at, str):
        scheduled_at = datetime.fromisoformat(scheduled_at)
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    
    return AppointmentResponse(
        appointment_id=appointment["appointment_id"],
        lead_id=appointment["lead_id"],
        lead_name=appointment.get("lead_name"),
        agent_id=appointment["agent_id"],
        agent_name=appointment.get("agent_name"),
        title=appointment["title"],
        description=appointment.get("description"),
        scheduled_at=scheduled_at,
        status=appointment["status"],
        created_at=created_at
    )


@router.delete("/{appointment_id}")
async def delete_appointment(appointment_id: str, request: Request):
    await get_current_user(request)
    
    result = await db.appointments.delete_one({"appointment_id": appointment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    return {"message": "Cita eliminada"}
