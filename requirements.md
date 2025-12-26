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

## Próximas Tareas
1. Integración real con WhatsApp vía N8N
2. Integración con Google Calendar
3. Notificaciones en tiempo real
4. Reportes exportables (PDF/Excel)
5. Sistema de permisos más granular
6. Personalización de marca (logo, colores)

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
