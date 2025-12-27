"""Lead management routes"""
import uuid
from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from datetime import datetime, timezone

import sys; sys.path.insert(0, "/app/backend"); from config import db, logger
from models.leads import LeadCreate, LeadUpdate, LeadResponse, ConversationCreate, ConversationResponse
from models.students import StudentResponse
from utils.auth import get_current_user, require_roles
from utils.helpers import find_agent_for_career, send_notification

router = APIRouter(prefix="/leads", tags=["leads"])


def generate_institutional_email(full_name: str) -> str:
    """Generate an institutional email from student name"""
    import unicodedata
    parts = full_name.lower().strip().split()
    if len(parts) >= 2:
        email_base = f"{parts[0]}.{parts[-1]}"
    else:
        email_base = parts[0] if parts else "estudiante"
    
    email_base = unicodedata.normalize('NFKD', email_base).encode('ASCII', 'ignore').decode()
    email_base = ''.join(c for c in email_base if c.isalnum() or c == '.')
    
    return f"{email_base}@ucic.edu.mx"


@router.post("", response_model=LeadResponse)
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


@router.get("", response_model=List[LeadResponse])
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


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: str, request: Request):
    await get_current_user(request)
    
    lead = await db.leads.find_one({"lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    # Get agent name
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


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: str, update_data: LeadUpdate, request: Request):
    await get_current_user(request)
    
    lead = await db.leads.find_one({"lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.leads.update_one({"lead_id": lead_id}, {"$set": update_dict})
    
    # Get updated lead
    lead = await db.leads.find_one({"lead_id": lead_id}, {"_id": 0})
    
    # Get agent name
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


@router.delete("/{lead_id}")
async def delete_lead(lead_id: str, request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    result = await db.leads.delete_one({"lead_id": lead_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    # Also delete conversations
    await db.conversations.delete_many({"lead_id": lead_id})
    
    return {"message": "Lead eliminado"}


@router.post("/{lead_id}/convert", response_model=StudentResponse)
async def convert_lead_to_student(lead_id: str, request: Request):
    """Convert a lead (in etapa_4_inscrito) to a student"""
    await require_roles(["admin", "gerente"])(request)
    body = await request.json()
    
    lead = await db.leads.find_one({"lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    if lead["status"] != "etapa_4_inscrito":
        raise HTTPException(status_code=400, detail="El lead debe estar en Etapa 4 - Inscrito para convertirlo en estudiante")
    
    # Check if already converted
    existing_student = await db.students.find_one({"lead_id": lead_id}, {"_id": 0})
    if existing_student:
        raise HTTPException(status_code=400, detail="Este lead ya fue convertido en estudiante")
    
    student_id = f"student_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    # Generate institutional email
    institutional_email = body.get("institutional_email")
    if not institutional_email:
        institutional_email = generate_institutional_email(lead["full_name"])
        base_email = institutional_email.replace("@ucic.edu.mx", "")
        counter = 1
        while await db.students.find_one({"institutional_email": institutional_email}, {"_id": 0}):
            institutional_email = f"{base_email}{counter}@ucic.edu.mx"
            counter += 1
    
    # Create document folder for student
    from pathlib import Path
    student_folder = Path("/app/student_documents") / student_id
    student_folder.mkdir(exist_ok=True)
    
    student = {
        "student_id": student_id,
        "full_name": lead["full_name"],
        "email": lead["email"],
        "phone": lead["phone"],
        "career_id": body.get("career_id", ""),
        "career_name": body.get("career_name", lead["career_interest"]),
        "institutional_email": institutional_email,
        "lead_id": lead_id,
        "documents": [],
        "attendance": [],
        "custom_fields": {},
        "is_active": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.students.insert_one(student)
    student.pop("_id", None)
    
    logger.info(f"Lead {lead_id} converted to student {student_id}")
    return StudentResponse(**student)


# Conversation endpoints
@router.get("/{lead_id}/conversations", response_model=ConversationResponse)
async def get_lead_conversations(lead_id: str, request: Request):
    await get_current_user(request)
    
    conversation = await db.conversations.find_one({"lead_id": lead_id}, {"_id": 0})
    if not conversation:
        # Create empty conversation
        conversation = {
            "conversation_id": f"conv_{uuid.uuid4().hex[:12]}",
            "lead_id": lead_id,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.conversations.insert_one(conversation)
        conversation.pop("_id", None)
    
    created_at = conversation.get("created_at")
    updated_at = conversation.get("updated_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    return ConversationResponse(
        conversation_id=conversation["conversation_id"],
        lead_id=conversation["lead_id"],
        messages=conversation["messages"],
        created_at=created_at,
        updated_at=updated_at
    )


@router.post("/{lead_id}/conversations", response_model=ConversationResponse)
async def add_message_to_conversation(lead_id: str, message_data: ConversationCreate, request: Request):
    await get_current_user(request)
    
    now = datetime.now(timezone.utc)
    new_message = {
        "sender": message_data.sender,
        "message": message_data.message,
        "timestamp": now.isoformat()
    }
    
    conversation = await db.conversations.find_one({"lead_id": lead_id}, {"_id": 0})
    if conversation:
        await db.conversations.update_one(
            {"lead_id": lead_id},
            {
                "$push": {"messages": new_message},
                "$set": {"updated_at": now.isoformat()}
            }
        )
    else:
        conversation = {
            "conversation_id": f"conv_{uuid.uuid4().hex[:12]}",
            "lead_id": lead_id,
            "messages": [new_message],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        await db.conversations.insert_one(conversation)
    
    conversation = await db.conversations.find_one({"lead_id": lead_id}, {"_id": 0})
    
    created_at = conversation.get("created_at")
    updated_at = conversation.get("updated_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    
    return ConversationResponse(
        conversation_id=conversation["conversation_id"],
        lead_id=conversation["lead_id"],
        messages=conversation["messages"],
        created_at=created_at,
        updated_at=updated_at
    )
