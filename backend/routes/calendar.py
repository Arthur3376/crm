"""Google Calendar integration routes"""
import uuid
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone, timedelta
import os

import sys; sys.path.insert(0, "/app/backend"); from config import db, logger, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_CALENDAR_SCOPES
from utils.auth import get_current_user

router = APIRouter(prefix="/auth/google/calendar", tags=["calendar"])


@router.get("/connect")
async def initiate_google_calendar_oauth(request: Request):
    """Initiate Google Calendar OAuth flow"""
    current_user = await get_current_user(request)
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google Calendar no está configurado")
    
    # Generate state token
    state = f"{current_user['user_id']}_{uuid.uuid4().hex[:8]}"
    
    # Store state in database
    await db.oauth_states.insert_one({
        "state": state,
        "user_id": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Get the callback URL from the frontend URL
    frontend_url = os.environ.get('FRONTEND_URL', '')
    if frontend_url:
        # Extract the base URL and use it for the callback
        callback_url = frontend_url.replace('https://', 'https://').rstrip('/') + '/api/auth/google/calendar/callback'
    else:
        callback_url = str(request.base_url).rstrip('/') + '/api/auth/google/calendar/callback'
    
    # Build authorization URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": " ".join(GOOGLE_CALENDAR_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    return {"auth_url": auth_url}


@router.get("/callback")
async def google_calendar_oauth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle Google Calendar OAuth callback"""
    import httpx
    
    if error:
        logger.error(f"Google Calendar OAuth error: {error}")
        frontend_url = os.environ.get('FRONTEND_URL', '')
        return RedirectResponse(url=f"{frontend_url}/calendar?error={error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Código o estado faltante")
    
    # Verify state
    oauth_state = await db.oauth_states.find_one({"state": state}, {"_id": 0})
    if not oauth_state:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    user_id = oauth_state["user_id"]
    
    # Clean up state
    await db.oauth_states.delete_one({"state": state})
    
    # Get the callback URL
    frontend_url = os.environ.get('FRONTEND_URL', '')
    if frontend_url:
        callback_url = frontend_url.replace('https://', 'https://').rstrip('/') + '/api/auth/google/calendar/callback'
    else:
        callback_url = str(request.base_url).rstrip('/') + '/api/auth/google/calendar/callback'
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": callback_url
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=token_data)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            return RedirectResponse(url=f"{frontend_url}/calendar?error=token_exchange_failed")
        
        tokens = response.json()
    
    # Store tokens
    now = datetime.now(timezone.utc)
    token_doc = {
        "user_id": user_id,
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "token_type": tokens["token_type"],
        "expires_at": (now + timedelta(seconds=tokens["expires_in"])).isoformat(),
        "scope": tokens.get("scope"),
        "created_at": now.isoformat()
    }
    
    # Upsert token document
    await db.google_calendar_tokens.update_one(
        {"user_id": user_id},
        {"$set": token_doc},
        upsert=True
    )
    
    logger.info(f"Google Calendar connected for user {user_id}")
    
    return RedirectResponse(url=f"{frontend_url}/calendar?connected=true")


@router.get("/status")
async def get_calendar_connection_status(request: Request):
    """Check if user has connected Google Calendar"""
    current_user = await get_current_user(request)
    
    token = await db.google_calendar_tokens.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    
    if token:
        # Check if token is expired
        expires_at = datetime.fromisoformat(token["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        is_expired = expires_at < datetime.now(timezone.utc)
        
        return {
            "connected": True,
            "is_expired": is_expired,
            "expires_at": token["expires_at"]
        }
    
    return {"connected": False}


@router.delete("/disconnect")
async def disconnect_google_calendar(request: Request):
    """Disconnect Google Calendar"""
    current_user = await get_current_user(request)
    
    await db.google_calendar_tokens.delete_one({"user_id": current_user["user_id"]})
    
    return {"message": "Google Calendar desconectado"}


@router.get("/events")
async def get_calendar_events(request: Request):
    """Get calendar events from Google Calendar"""
    import httpx
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    current_user = await get_current_user(request)
    
    token = await db.google_calendar_tokens.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not token:
        raise HTTPException(status_code=400, detail="Google Calendar no conectado")
    
    # Check if token needs refresh
    expires_at = datetime.fromisoformat(token["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    access_token = token["access_token"]
    
    if expires_at < datetime.now(timezone.utc):
        # Refresh token
        if not token.get("refresh_token"):
            raise HTTPException(status_code=400, detail="Token expirado, reconecta Google Calendar")
        
        token_url = "https://oauth2.googleapis.com/token"
        refresh_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=refresh_data)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="No se pudo refrescar el token")
            
            new_tokens = response.json()
            access_token = new_tokens["access_token"]
            
            # Update stored token
            now = datetime.now(timezone.utc)
            await db.google_calendar_tokens.update_one(
                {"user_id": current_user["user_id"]},
                {"$set": {
                    "access_token": access_token,
                    "expires_at": (now + timedelta(seconds=new_tokens["expires_in"])).isoformat()
                }}
            )
    
    # Get events from Google Calendar
    try:
        credentials = Credentials(
            token=access_token,
            refresh_token=token.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        service = build("calendar", "v3", credentials=credentials)
        
        # Get events for the next 30 days
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=30)).isoformat()
        
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = events_result.get("items", [])
        
        return {"events": events}
    
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos: {str(e)}")


@router.post("/events")
async def create_calendar_event(request: Request):
    """Create a new event in Google Calendar"""
    import httpx
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    current_user = await get_current_user(request)
    body = await request.json()
    
    token = await db.google_calendar_tokens.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not token:
        raise HTTPException(status_code=400, detail="Google Calendar no conectado")
    
    # Get access token (refresh if needed)
    expires_at = datetime.fromisoformat(token["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    access_token = token["access_token"]
    
    if expires_at < datetime.now(timezone.utc):
        if not token.get("refresh_token"):
            raise HTTPException(status_code=400, detail="Token expirado, reconecta Google Calendar")
        
        token_url = "https://oauth2.googleapis.com/token"
        refresh_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=refresh_data)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="No se pudo refrescar el token")
            
            new_tokens = response.json()
            access_token = new_tokens["access_token"]
            
            now = datetime.now(timezone.utc)
            await db.google_calendar_tokens.update_one(
                {"user_id": current_user["user_id"]},
                {"$set": {
                    "access_token": access_token,
                    "expires_at": (now + timedelta(seconds=new_tokens["expires_in"])).isoformat()
                }}
            )
    
    try:
        credentials = Credentials(
            token=access_token,
            refresh_token=token.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        service = build("calendar", "v3", credentials=credentials)
        
        event = {
            "summary": body.get("title", "Cita UCIC"),
            "description": body.get("description", ""),
            "start": {
                "dateTime": body["start"],
                "timeZone": "America/Mexico_City"
            },
            "end": {
                "dateTime": body["end"],
                "timeZone": "America/Mexico_City"
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                    {"method": "email", "minutes": 60}
                ]
            }
        }
        
        if body.get("attendees"):
            event["attendees"] = [{"email": email} for email in body["attendees"]]
        
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        
        return {
            "success": True,
            "event_id": created_event["id"],
            "html_link": created_event.get("htmlLink")
        }
    
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear evento: {str(e)}")
