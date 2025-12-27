"""Dashboard routes"""
from fastapi import APIRouter, Request
from datetime import datetime, timezone, timedelta

from config import db
from models.dashboard import DashboardStats
from utils.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(request: Request):
    current_user = await get_current_user(request)
    
    # Base query for role-based filtering
    base_query = {}
    if current_user["role"] == "agente":
        base_query["assigned_agent_id"] = current_user["user_id"]
    
    # Total leads
    total_leads = await db.leads.count_documents(base_query)
    
    # Leads by status
    pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_results = await db.leads.aggregate(pipeline).to_list(100)
    leads_by_status = {r["_id"]: r["count"] for r in status_results}
    
    # Leads by source
    pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]
    source_results = await db.leads.aggregate(pipeline).to_list(100)
    leads_by_source = {r["_id"]: r["count"] for r in source_results}
    
    # Leads by career
    pipeline = [
        {"$match": base_query},
        {"$group": {"_id": "$career_interest", "count": {"$sum": 1}}}
    ]
    career_results = await db.leads.aggregate(pipeline).to_list(100)
    leads_by_career = {r["_id"]: r["count"] for r in career_results}
    
    # Leads by agent (only for admin/gerente)
    leads_by_agent = {}
    if current_user["role"] in ["admin", "gerente"]:
        pipeline = [
            {"$match": {"assigned_agent_id": {"$ne": None}}},
            {"$group": {"_id": "$assigned_agent_id", "count": {"$sum": 1}}}
        ]
        agent_results = await db.leads.aggregate(pipeline).to_list(100)
        
        # Get agent names
        agent_ids = [r["_id"] for r in agent_results]
        agents = await db.users.find({"user_id": {"$in": agent_ids}}, {"_id": 0}).to_list(1000)
        agent_map = {a["user_id"]: a["name"] for a in agents}
        
        leads_by_agent = {agent_map.get(r["_id"], r["_id"]): r["count"] for r in agent_results}
    
    # Conversion rate (etapa_4_inscrito / total)
    converted = leads_by_status.get("etapa_4_inscrito", 0)
    conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
    
    # Today's stats
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_query = {**base_query, "created_at": {"$gte": today_start.isoformat()}}
    new_leads_today = await db.leads.count_documents(today_query)
    
    # Today's appointments
    today_end = today_start + timedelta(days=1)
    apt_query = {
        "scheduled_at": {
            "$gte": today_start.isoformat(),
            "$lt": today_end.isoformat()
        }
    }
    if current_user["role"] == "agente":
        apt_query["agent_id"] = current_user["user_id"]
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


@router.get("/careers")
async def get_career_options(request: Request):
    """Get list of careers for dropdowns"""
    await get_current_user(request)
    
    # First check if there are custom careers
    careers_doc = await db.settings.find_one({"type": "careers"}, {"_id": 0})
    
    if careers_doc and careers_doc.get("items"):
        return {"careers": careers_doc["items"]}
    
    # Fall back to careers from careers_full collection
    careers = await db.careers_full.find({"is_active": True}, {"_id": 0, "name": 1}).to_list(1000)
    career_names = [c["name"] for c in careers]
    
    if career_names:
        return {"careers": career_names}
    
    # Fall back to default careers
    from config import DEFAULT_CAREERS
    return {"careers": DEFAULT_CAREERS}


@router.get("/sources")
async def get_source_options(request: Request):
    """Get list of lead sources for dropdowns"""
    await get_current_user(request)
    from config import LEAD_SOURCES
    return {"sources": LEAD_SOURCES}


@router.get("/statuses")
async def get_status_options(request: Request):
    """Get list of lead statuses for dropdowns"""
    await get_current_user(request)
    from config import LEAD_STATUSES
    return {"statuses": LEAD_STATUSES}
