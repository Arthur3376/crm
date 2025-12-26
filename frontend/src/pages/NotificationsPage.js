import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import {
  Bell,
  Phone,
  Webhook,
  Save,
  Send,
  CheckCircle,
  AlertCircle,
  MessageSquare
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function NotificationsPage() {
  const [settings, setSettings] = useState({
    notification_phone: '',
    notification_webhook_url: '',
    notify_on_new_lead: true,
    notify_on_appointment: true,
    notify_supervisors: false
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [whatsappStatus, setWhatsappStatus] = useState({
    configured: false,
    account_sid: null,
    whatsapp_number: null
  });

  useEffect(() => {
    fetchSettings();
    fetchWhatsAppStatus();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/settings/notifications`, { withCredentials: true });
      setSettings({
        notification_phone: response.data.notification_phone || '',
        notification_webhook_url: response.data.notification_webhook_url || '',
        notify_on_new_lead: response.data.notify_on_new_lead,
        notify_on_appointment: response.data.notify_on_appointment,
        notify_supervisors: response.data.notify_supervisors
      });
    } catch (error) {
      console.error('Error fetching settings:', error);
      toast.error('Error al cargar configuración');
    } finally {
      setLoading(false);
    }
  };

  const fetchWhatsAppStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/whatsapp/status`, { withCredentials: true });
      setWhatsappStatus(response.data);
    } catch (error) {
      console.error('Error fetching WhatsApp status:', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API_URL}/api/settings/notifications`, settings, { withCredentials: true });
      toast.success('Configuración guardada');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const handleTestNotification = async () => {
    if (!settings.notification_phone) {
      toast.error('Configura un número de WhatsApp primero');
      return;
    }
    
    setTesting(true);
    try {
      await axios.post(`${API_URL}/api/settings/notifications/test`, {}, { withCredentials: true });
      toast.success('Notificación de prueba enviada a WhatsApp');
    } catch (error) {
      toast.error('Error al enviar notificación de prueba');
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" data-testid="notifications-loading">
        <div className="h-12 bg-slate-200 rounded-md w-1/3" />
        <div className="h-64 bg-slate-200 rounded-md" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="notifications-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Notificaciones
          </h1>
          <p className="text-slate-500 mt-1">
            Configura alertas cuando lleguen nuevos leads
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleTestNotification}
            disabled={testing || !settings.notification_webhook_url}
            data-testid="test-notification-btn"
          >
            {testing ? (
              <div className="w-4 h-4 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin mr-2" />
            ) : (
              <Send className="w-4 h-4 mr-2" />
            )}
            Probar
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving}
            className="bg-slate-900 hover:bg-slate-800"
            data-testid="save-notifications-btn"
          >
            {saving ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Guardar
          </Button>
        </div>
      </div>

      {/* WhatsApp Status Card */}
      <Card className={whatsappStatus.configured ? "border-emerald-200 bg-emerald-50/50" : "border-amber-200 bg-amber-50/50"}>
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <MessageSquare className={`w-5 h-5 ${whatsappStatus.configured ? 'text-emerald-600' : 'text-amber-600'} mt-0.5`} />
            <div className="flex-1">
              <h3 className={`font-medium ${whatsappStatus.configured ? 'text-emerald-900' : 'text-amber-900'}`}>
                WhatsApp via Twilio
              </h3>
              {whatsappStatus.configured ? (
                <div className="mt-1">
                  <p className="text-sm text-emerald-700 flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" />
                    Conectado - Número: {whatsappStatus.whatsapp_number}
                  </p>
                  <p className="text-xs text-emerald-600 mt-1">
                    Account SID: {whatsappStatus.account_sid}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-amber-700 mt-1">
                  Twilio no está configurado. Contacta al administrador para configurar las credenciales.
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="border-blue-200 bg-blue-50/50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Bell className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-blue-900">Cómo funcionan las notificaciones</h3>
              <p className="text-sm text-blue-700 mt-1">
                Cuando llegue un nuevo lead, enviaremos una notificación directamente a WhatsApp usando Twilio.
                También puedes configurar un webhook para N8N como respaldo.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Settings Card */}
      <Card data-testid="notification-settings-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Phone className="w-5 h-5" />
            Configuración de Notificaciones
          </CardTitle>
          <CardDescription>
            Define el número y URL para recibir alertas de nuevos leads
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Phone Number */}
          <div className="space-y-2">
            <Label htmlFor="notification_phone" className="flex items-center gap-2">
              <Phone className="w-4 h-4 text-slate-500" />
              Número de WhatsApp para notificaciones
            </Label>
            <Input
              id="notification_phone"
              type="tel"
              placeholder="+521234567890"
              value={settings.notification_phone}
              onChange={(e) => setSettings(prev => ({ ...prev, notification_phone: e.target.value }))}
              className="max-w-md"
              data-testid="input-notification-phone"
            />
            <p className="text-xs text-slate-500">
              Este número se incluirá en el payload del webhook para que N8N pueda enviar el mensaje
            </p>
          </div>

          {/* Webhook URL */}
          <div className="space-y-2">
            <Label htmlFor="notification_webhook_url" className="flex items-center gap-2">
              <Webhook className="w-4 h-4 text-slate-500" />
              URL del Webhook (N8N)
            </Label>
            <Input
              id="notification_webhook_url"
              type="url"
              placeholder="https://tu-n8n.com/webhook/notificaciones"
              value={settings.notification_webhook_url}
              onChange={(e) => setSettings(prev => ({ ...prev, notification_webhook_url: e.target.value }))}
              className="max-w-xl"
              data-testid="input-webhook-url"
            />
            <p className="text-xs text-slate-500">
              URL del webhook en N8N donde enviaremos las notificaciones de nuevos leads
            </p>
          </div>

          {/* Toggle Options */}
          <div className="space-y-4 pt-4 border-t">
            <h4 className="font-medium text-slate-900">Eventos a notificar</h4>
            
            <div className="flex items-center justify-between max-w-md">
              <div className="space-y-0.5">
                <Label htmlFor="notify_new_lead" className="font-normal">Nuevo lead creado</Label>
                <p className="text-xs text-slate-500">Recibe alerta cuando llegue un nuevo lead</p>
              </div>
              <Switch
                id="notify_new_lead"
                checked={settings.notify_on_new_lead}
                onCheckedChange={(checked) => setSettings(prev => ({ ...prev, notify_on_new_lead: checked }))}
                data-testid="switch-new-lead"
              />
            </div>

            <div className="flex items-center justify-between max-w-md">
              <div className="space-y-0.5">
                <Label htmlFor="notify_appointment" className="font-normal">Cita agendada</Label>
                <p className="text-xs text-slate-500">Recibe alerta cuando se agende una cita</p>
              </div>
              <Switch
                id="notify_appointment"
                checked={settings.notify_on_appointment}
                onCheckedChange={(checked) => setSettings(prev => ({ ...prev, notify_on_appointment: checked }))}
                data-testid="switch-appointment"
              />
            </div>

            <div className="flex items-center justify-between max-w-md">
              <div className="space-y-0.5">
                <Label htmlFor="notify_supervisors" className="font-normal">Notificar a supervisores</Label>
                <p className="text-xs text-slate-500">También enviar notificación a supervisores</p>
              </div>
              <Switch
                id="notify_supervisors"
                checked={settings.notify_supervisors}
                onCheckedChange={(checked) => setSettings(prev => ({ ...prev, notify_supervisors: checked }))}
                data-testid="switch-supervisors"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Webhook Payload Example */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Formato del Payload de Notificación</CardTitle>
          <CardDescription>
            Este es el formato JSON que recibirás en tu webhook de N8N
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="bg-slate-50 p-4 rounded-md text-sm overflow-x-auto">
{`{
  "event": "lead.created",
  "phone": "${settings.notification_phone || '+521234567890'}",
  "message": "🔔 *Nuevo Lead*\\n\\n👤 *Nombre:* Juan Pérez\\n📧 *Email:* juan@ejemplo.com\\n📱 *Teléfono:* +521234567890\\n🎓 *Carrera:* Ingeniería\\n📍 *Fuente:* facebook",
  "lead": {
    "lead_id": "lead_abc123",
    "full_name": "Juan Pérez",
    "email": "juan@ejemplo.com",
    "phone": "+521234567890",
    "career_interest": "Ingeniería",
    "source": "facebook"
  },
  "agent": {
    "name": "Admin Demo",
    "email": "admin@leadflow.com"
  },
  "timestamp": "2025-01-01T12:00:00Z"
}`}
          </pre>
          <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-md flex items-start gap-2">
            <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div className="text-sm text-emerald-800">
              <strong>Tip:</strong> En N8N puedes usar el campo <code>message</code> directamente para enviar por WhatsApp,
              o construir tu propio mensaje usando los datos del <code>lead</code>.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
