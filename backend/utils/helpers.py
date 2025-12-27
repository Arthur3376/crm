"""Helper utilities"""
import uuid
import httpx
from typing import Optional
from datetime import datetime, timezone
from fastapi import Request

import sys; sys.path.insert(0, "/app/backend"); from config import db, logger, twilio_client, TWILIO_WHATSAPP_NUMBER


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


async def create_audit_log(
    entity_type: str,
    entity_id: str,
    action: str,
    performed_by: dict,
    request: Request,
    field_changed: Optional[str] = None,
    old_value=None,
    new_value=None,
    authorized_by: Optional[dict] = None
):
    """Create an audit log entry"""
    log_id = f"log_{uuid.uuid4().hex[:12]}"
    
    # Get client IP
    ip_address = request.client.host if request.client else None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    
    log_entry = {
        "log_id": log_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "field_changed": field_changed,
        "old_value": str(old_value) if old_value is not None else None,
        "new_value": str(new_value) if new_value is not None else None,
        "performed_by_id": performed_by["user_id"],
        "performed_by_name": performed_by["name"],
        "performed_by_role": performed_by["role"],
        "authorized_by_id": authorized_by["user_id"] if authorized_by else None,
        "authorized_by_name": authorized_by["name"] if authorized_by else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_address": ip_address
    }
    
    await db.audit_logs.insert_one(log_entry)
    return log_entry


async def send_notification(event: str, data: dict, agent_data: Optional[dict] = None):
    """Send notification via webhook and optionally WhatsApp"""
    try:
        # Get notification settings
        settings = await db.notification_settings.find_one({}, {"_id": 0})
        
        if not settings:
            logger.info("No notification settings configured")
            return
        
        # Send to N8N webhook if configured
        webhook_url = settings.get("notification_webhook_url")
        if webhook_url and settings.get("notify_on_new_lead", True):
            try:
                payload = {
                    "event": event,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": data
                }
                if agent_data:
                    payload["assigned_agent"] = agent_data
                
                logger.info(f"Sending webhook to: {webhook_url}")
                async with httpx.AsyncClient() as client:
                    response = await client.post(webhook_url, json=payload, timeout=5.0)
                    logger.info(f"Webhook notification sent: {response.status_code} - {response.text[:100] if response.text else 'No response body'}")
            except httpx.TimeoutException:
                logger.error(f"Webhook timeout - server not responding: {webhook_url}")
            except httpx.ConnectError as e:
                logger.error(f"Webhook connection error: {webhook_url} - {str(e)}")
            except Exception as e:
                logger.error(f"Failed to send webhook notification: {type(e).__name__} - {str(e)}")
        
        # Send WhatsApp notification if configured
        notification_phone = settings.get("notification_phone")
        if notification_phone and twilio_client and settings.get("notify_on_new_lead", True):
            try:
                if event == "lead.created":
                    message_body = f"🆕 Nuevo Lead!\n\nNombre: {data.get('full_name')}\nEmail: {data.get('email')}\nTeléfono: {data.get('phone')}\nCarrera: {data.get('career_interest')}\nFuente: {data.get('source')}"
                    
                    if agent_data:
                        message_body += f"\n\nAsignado a: {agent_data.get('name')}"
                    
                    message = twilio_client.messages.create(
                        body=message_body,
                        from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                        to=f"whatsapp:{notification_phone}"
                    )
                    logger.info(f"WhatsApp notification sent: {message.sid}")
            except Exception as e:
                logger.error(f"Failed to send WhatsApp notification: {e}")
    
    except Exception as e:
        logger.error(f"Error in send_notification: {e}")
