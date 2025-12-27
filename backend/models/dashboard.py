"""Dashboard-related Pydantic models"""
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_leads: int
    leads_by_status: dict
    leads_by_source: dict
    leads_by_career: dict
    leads_by_agent: dict
    conversion_rate: float
    new_leads_today: int
    appointments_today: int
