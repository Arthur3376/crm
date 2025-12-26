# LeadFlow Pro - Sistema de Gestión de Leads

## Requisitos Originales
Sistema web para gestión de leads de redes sociales (Facebook, Instagram, TikTok) con:
- Registro de leads con datos: nombre completo, correo, teléfono, carrera de interés
- Sistema de usuarios con 4 niveles (Admin, Gerente, Supervisor, Agente)
- Historial de conversaciones por lead
- Integración con N8N para WhatsApp
- Dashboard con métricas y visualizaciones
- Calendario de citas/seguimientos

## Arquitectura Implementada

### Backend (FastAPI + MongoDB)
- **Autenticación**: JWT + Google OAuth (Emergent Auth)
- **Modelos**: Users, Leads, Conversations, Appointments, Webhooks
- **Endpoints API**:
  - `/api/auth/*` - Registro, login, logout, sesión Google
  - `/api/leads/*` - CRUD completo de leads
  - `/api/users/*` - Gestión de usuarios
  - `/api/conversations/*` - Historial de mensajes
  - `/api/appointments/*` - Calendario de citas
  - `/api/webhooks/*` - Configuración webhooks
  - `/api/dashboard/*` - Métricas y estadísticas
  - `/api/webhooks/incoming/lead` - Endpoint para N8N

### Frontend (React + Tailwind + Shadcn)
- **Páginas**: Login, Dashboard, Leads, LeadDetail, Users, Calendar, Webhooks
- **Diseño**: Profesional/corporativo con colores slate/blue

## Tareas Completadas
1. ✅ Login con email/password y Google OAuth
2. ✅ Dashboard con KPIs y gráficos (Recharts)
3. ✅ CRUD completo de leads con filtros
4. ✅ Detalle de lead con historial de conversación
5. ✅ Calendario de citas
6. ✅ Gestión de usuarios con 4 roles
7. ✅ Webhooks para integración N8N
8. ✅ API endpoint público para recibir leads externos
9. ✅ Sistema de notificaciones configurable (número WhatsApp + webhook N8N)
10. ✅ **Integración WhatsApp via Twilio** - Envía notificaciones directas por WhatsApp
11. ✅ **Integración Google Calendar** - Sincroniza citas con el calendario de Google

## Configuración de Integraciones

### WhatsApp (Twilio)
Variables de entorno en `/app/backend/.env`:
```
TWILIO_ACCOUNT_SID="tu_account_sid"
TWILIO_AUTH_TOKEN="tu_auth_token"
TWILIO_WHATSAPP_NUMBER="+14155238886"
```

**Para Sandbox de Twilio:**
1. El usuario debe enviar "join <código>" al número de WhatsApp de Twilio
2. Luego podrá recibir notificaciones

### Google Calendar
Variables de entorno en `/app/backend/.env`:
```
GOOGLE_CLIENT_ID="tu_client_id"
GOOGLE_CLIENT_SECRET="tu_client_secret"
```

**Para configurar:**
1. Ve a https://console.cloud.google.com
2. Crea un proyecto y habilita "Google Calendar API"
3. Crea credenciales OAuth 2.0 (Web application)
4. Añade redirect URI: `{TU_URL}/api/auth/google/calendar/callback`
5. Copia Client ID y Client Secret al .env

## Próximas Tareas
1. Reportes exportables (PDF/Excel)
2. Sistema de permisos más granular
3. Personalización de marca (logo, colores)

## Credenciales de Prueba
- Email: admin@leadflow.com
- Password: admin123

## Endpoint N8N
```
POST /api/webhooks/incoming/lead
{
  "full_name": "Nombre",
  "email": "email@ejemplo.com",
  "phone": "+521234567890",
  "career_interest": "Ingeniería",
  "source": "facebook",
  "source_detail": "Campaña Verano"
}
```
