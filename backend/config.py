"""Application configuration and database setup"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'leadflow-pro-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')

# Google Calendar Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/userinfo.email"]

# Resend Email Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        from twilio.rest import Client as TwilioClient
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")

# Initialize Resend
if RESEND_API_KEY:
    import resend
    resend.api_key = RESEND_API_KEY
    logger.info("Resend email client configured")

# Constants
USER_ROLES = ["admin", "gerente", "supervisor", "agente", "maestro"]
LEAD_SOURCES = ["facebook", "instagram", "tiktok", "manual", "webhook"]
LEAD_STATUSES = ["etapa_1_informacion", "etapa_2_contacto", "etapa_3_documentacion", "etapa_4_inscrito"]
DEFAULT_CAREERS = ["Ingeniería", "Medicina", "Derecho", "Administración", "Contabilidad", "Psicología", "Diseño", "Marketing", "Otra"]
NOTIFICATION_EVENTS = ["lead.created", "lead.updated", "appointment.created", "appointment.reminder"]

# Paths
STUDENT_DOCUMENTS_PATH = Path("/app/student_documents")
STUDENT_DOCUMENTS_PATH.mkdir(exist_ok=True)
