"""Webhook and notification routes"""
import uuid
import secrets
from fastapi import APIRouter, HTTPException, Request
from typing import List
from datetime import datetime, timezone

import sys; sys.path.insert(0, "/app/backend"); from config import db, logger
from models.webhooks import (
    WebhookCreate, WebhookResponse,
    NotificationSettingsUpdate, NotificationSettingsResponse,
    N8NLeadPayload
)
from utils.auth import get_current_user, require_roles
from utils.helpers import find_agent_for_career, send_notification

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(webhook_data: WebhookCreate, request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    webhook_id = f"webhook_{uuid.uuid4().hex[:12]}"
    secret_key = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    
    webhook = {
        "webhook_id": webhook_id,
        "name": webhook_data.name,
        "url": webhook_data.url,
        "events": webhook_data.events,
        "is_active": webhook_data.is_active,
        "secret_key": secret_key,
        "created_at": now.isoformat()
    }
    
    await db.webhooks.insert_one(webhook)
    webhook.pop("_id", None)
    
    return WebhookResponse(
        webhook_id=webhook_id,
        name=webhook_data.name,
        url=webhook_data.url,
        events=webhook_data.events,
        is_active=webhook_data.is_active,
        secret_key=secret_key,
        created_at=now
    )


@router.get("/webhooks", response_model=List[WebhookResponse])
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


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, request: Request):
    await require_roles(["admin"])(request)
    
    result = await db.webhooks.delete_one({"webhook_id": webhook_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webhook no encontrado")
    
    return {"message": "Webhook eliminado"}


# N8N Webhook endpoint for receiving leads
@router.post("/webhook/n8n/lead")
async def receive_n8n_lead(payload: N8NLeadPayload):
    """Receive lead from N8N webhook"""
    lead_id = f"lead_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    # Try to find an agent for this career
    career_agent = await find_agent_for_career(payload.career_interest)
    assigned_agent_id = career_agent["user_id"] if career_agent else None
    
    lead_doc = {
        "lead_id": lead_id,
        "full_name": payload.full_name,
        "email": payload.email,
        "phone": payload.phone,
        "career_interest": payload.career_interest,
        "source": payload.source,
        "source_detail": payload.source_detail or "N8N Webhook",
        "status": "nuevo",
        "assigned_agent_id": assigned_agent_id,
        "notes": None,
        "created_at": now,
        "updated_at": now,
        "created_by": "n8n_webhook"
    }
    
    await db.leads.insert_one(lead_doc)
    
    # Get agent data for notification
    agent_data = None
    if assigned_agent_id and career_agent:
        agent_data = {"name": career_agent["name"], "email": career_agent.get("email"), "phone": career_agent.get("phone")}
    
    # Send notification
    await send_notification("lead.created", {
        "lead_id": lead_id,
        "full_name": payload.full_name,
        "email": payload.email,
        "phone": payload.phone,
        "career_interest": payload.career_interest,
        "source": payload.source,
        "source_detail": payload.source_detail
    }, agent_data)
    
    logger.info(f"Lead created from N8N webhook: {lead_id}")
    
    return {
        "success": True,
        "lead_id": lead_id,
        "message": "Lead creado exitosamente",
        "assigned_agent": agent_data
    }


# Notification Settings
@router.get("/settings/notifications", response_model=NotificationSettingsResponse)
async def get_notification_settings(request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    settings = await db.notification_settings.find_one({}, {"_id": 0})
    
    if not settings:
        # Create default settings
        settings = {
            "settings_id": f"settings_{uuid.uuid4().hex[:8]}",
            "notification_phone": None,
            "notification_webhook_url": None,
            "notify_on_new_lead": True,
            "notify_on_appointment": True,
            "notify_supervisors": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notification_settings.insert_one(settings)
        settings.pop("_id", None)
    
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


@router.put("/settings/notifications", response_model=NotificationSettingsResponse)
async def update_notification_settings(settings_data: NotificationSettingsUpdate, request: Request):
    await require_roles(["admin", "gerente"])(request)
    
    now = datetime.now(timezone.utc)
    
    existing = await db.notification_settings.find_one({}, {"_id": 0})
    
    update_data = settings_data.model_dump()
    update_data["updated_at"] = now.isoformat()
    
    if existing:
        await db.notification_settings.update_one({}, {"$set": update_data})
    else:
        update_data["settings_id"] = f"settings_{uuid.uuid4().hex[:8]}"
        await db.notification_settings.insert_one(update_data)
    
    settings = await db.notification_settings.find_one({}, {"_id": 0})
    
    return NotificationSettingsResponse(
        settings_id=settings["settings_id"],
        notification_phone=settings.get("notification_phone"),
        notification_webhook_url=settings.get("notification_webhook_url"),
        notify_on_new_lead=settings.get("notify_on_new_lead", True),
        notify_on_appointment=settings.get("notify_on_appointment", True),
        notify_supervisors=settings.get("notify_supervisors", False),
        updated_at=now
    )
