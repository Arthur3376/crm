"""
UCIC API Server - Modular Architecture
Main entry point for the FastAPI application
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from config import db, logger

# Import the main API router with all routes included
from routes import api_router

# Create the main app
app = FastAPI(title="UCIC API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://campus-flow-8.preview.emergentagent.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router)


# Health check endpoint
@app.get("/")
async def root():
    return {"status": "healthy", "app": "UCIC API", "version": "2.0.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


# Initialize database indexes on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting UCIC API...")
    
    # Create indexes for better performance
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("user_id", unique=True)
        await db.leads.create_index("lead_id", unique=True)
        await db.leads.create_index("email")
        await db.leads.create_index("assigned_agent_id")
        await db.leads.create_index("status")
        await db.students.create_index("student_id", unique=True)
        await db.students.create_index("email")
        await db.students.create_index("institutional_email", unique=True, sparse=True)
        await db.teachers.create_index("teacher_id", unique=True)
        await db.teachers.create_index("email", unique=True)
        await db.careers_full.create_index("career_id", unique=True)
        await db.appointments.create_index("appointment_id", unique=True)
        await db.appointments.create_index("scheduled_at")
        await db.custom_fields.create_index("field_id", unique=True)
        await db.change_requests.create_index("request_id", unique=True)
        await db.audit_logs.create_index("timestamp")
        await db.audit_logs.create_index("entity_id")
        logger.info("Database indexes created/verified")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")
    
    # Ensure default settings exist
    careers_doc = await db.settings.find_one({"type": "careers"}, {"_id": 0})
    if not careers_doc:
        from config import DEFAULT_CAREERS
        await db.settings.insert_one({
            "type": "careers",
            "items": DEFAULT_CAREERS
        })
        logger.info("Default careers initialized")
    
    logger.info("UCIC API started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down UCIC API...")
