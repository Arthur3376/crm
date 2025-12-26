import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';
import {
  Plus,
  Trash2,
  Webhook,
  Copy,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const WEBHOOK_EVENTS = [
  { value: 'lead.created', label: 'Lead Creado' },
  { value: 'lead.updated', label: 'Lead Actualizado' },
  { value: 'lead.deleted', label: 'Lead Eliminado' },
  { value: 'appointment.created', label: 'Cita Creada' },
  { value: 'appointment.updated', label: 'Cita Actualizada' }
];

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    events: [],
    is_active: true
  });

  useEffect(() => {
    fetchWebhooks();
  }, []);

  const fetchWebhooks = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/webhooks`, { withCredentials: true });
      setWebhooks(response.data);
    } catch (error) {
      console.error('Error fetching webhooks:', error);
      toast.error('Error al cargar los webhooks');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWebhook = async (e) => {
    e.preventDefault();
    if (formData.events.length === 0) {
      toast.error('Selecciona al menos un evento');
      return;
    }
    
    try {
      await axios.post(`${API_URL}/api/webhooks`, formData, { withCredentials: true });
      toast.success('Webhook creado exitosamente');
      setShowCreateModal(false);
      setFormData({ name: '', url: '', events: [], is_active: true });
      fetchWebhooks();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear el webhook');
    }
  };

  const handleDeleteWebhook = async (webhookId) => {
    if (!window.confirm('¿Estás seguro de eliminar este webhook?')) return;
    
    try {
      await axios.delete(`${API_URL}/api/webhooks/${webhookId}`, { withCredentials: true });
      toast.success('Webhook eliminado');
      fetchWebhooks();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copiado al portapapeles');
  };

  const toggleEvent = (event) => {
    setFormData(prev => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter(e => e !== event)
        : [...prev.events, event]
    }));
  };

  const incomingWebhookUrl = `${API_URL}/api/webhooks/incoming/lead`;

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" data-testid="webhooks-loading">
        <div className="h-12 bg-slate-200 rounded-md w-1/3" />
        <div className="h-48 bg-slate-200 rounded-md" />
        <div className="h-64 bg-slate-200 rounded-md" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="webhooks-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Webhooks
          </h1>
          <p className="text-slate-500 mt-1">
            Configura integraciones con N8N y otros servicios
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="bg-slate-900 hover:bg-slate-800 text-white"
          data-testid="create-webhook-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Webhook
        </Button>
      </div>

      {/* Incoming Webhook (for N8N) */}
      <Card className="border-blue-200 bg-blue-50/50" data-testid="incoming-webhook-card">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Webhook className="w-5 h-5 text-blue-600" />
            <CardTitle className="text-lg text-blue-900">Webhook de Entrada para N8N</CardTitle>
          </div>
          <CardDescription className="text-blue-700">
            Usa esta URL en N8N para enviar leads desde WhatsApp, Facebook, Instagram o TikTok
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label className="text-blue-800 mb-2 block">URL del Webhook</Label>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-white px-3 py-2 rounded-md border border-blue-200 text-sm font-mono text-slate-800 overflow-x-auto">
                  {incomingWebhookUrl}
                </code>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => copyToClipboard(incomingWebhookUrl)}
                  className="shrink-0"
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            <div className="bg-white rounded-md border border-blue-200 p-4">
              <h4 className="font-medium text-slate-900 mb-2">Formato del Payload (JSON)</h4>
              <pre className="bg-slate-50 p-3 rounded text-xs overflow-x-auto">
{`{
  "full_name": "Nombre del Lead",
  "email": "email@ejemplo.com",
  "phone": "+521234567890",
  "career_interest": "Ingeniería",
  "source": "facebook", // facebook, instagram, tiktok, webhook
  "source_detail": "Campaña Verano 2024",
  "whatsapp_number": "+521234567890"
}`}
              </pre>
            </div>

            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-md">
              <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <strong>Nota:</strong> Este endpoint es público para recibir datos de N8N. 
                Los leads creados aparecerán automáticamente en la lista sin agente asignado.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Outgoing Webhooks */}
      <Card data-testid="outgoing-webhooks-card">
        <CardHeader>
          <CardTitle className="text-lg">Webhooks de Salida</CardTitle>
          <CardDescription>
            Recibe notificaciones cuando ocurran eventos en el sistema
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {webhooks.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="font-medium">Nombre</TableHead>
                  <TableHead className="font-medium">URL</TableHead>
                  <TableHead className="font-medium">Eventos</TableHead>
                  <TableHead className="font-medium">Estado</TableHead>
                  <TableHead className="font-medium">Secret Key</TableHead>
                  <TableHead className="text-right font-medium">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {webhooks.map((webhook) => (
                  <TableRow key={webhook.webhook_id} className="table-row-hover" data-testid={`webhook-row-${webhook.webhook_id}`}>
                    <TableCell className="font-medium text-slate-900">
                      {webhook.name}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-600 truncate max-w-[200px]">
                          {webhook.url}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => window.open(webhook.url, '_blank')}
                        >
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {webhook.events.map(event => (
                          <span key={event} className="pill-badge bg-slate-100 text-slate-700 border border-slate-200">
                            {WEBHOOK_EVENTS.find(e => e.value === event)?.label || event}
                          </span>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      {webhook.is_active ? (
                        <span className="flex items-center gap-1 text-emerald-600">
                          <CheckCircle className="w-4 h-4" />
                          Activo
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-slate-500">
                          <XCircle className="w-4 h-4" />
                          Inactivo
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <code className="text-xs bg-slate-100 px-2 py-1 rounded truncate max-w-[120px]">
                          {webhook.secret_key}
                        </code>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => copyToClipboard(webhook.secret_key)}
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteWebhook(webhook.webhook_id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="empty-state py-12">
              <Webhook className="empty-state-icon" />
              <h3 className="text-lg font-medium text-slate-900 mb-1">No hay webhooks</h3>
              <p className="text-slate-500 mb-4">Crea un webhook para recibir notificaciones</p>
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Nuevo Webhook
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Webhook Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-md" data-testid="create-webhook-modal">
          <DialogHeader>
            <DialogTitle>Nuevo Webhook</DialogTitle>
            <DialogDescription>
              Configura una URL para recibir notificaciones de eventos
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateWebhook} className="space-y-4">
            <div className="form-group">
              <Label htmlFor="name">Nombre *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Ej: N8N Notificaciones"
                required
                data-testid="input-webhook-name"
              />
            </div>
            <div className="form-group">
              <Label htmlFor="url">URL del Webhook *</Label>
              <Input
                id="url"
                type="url"
                value={formData.url}
                onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                placeholder="https://n8n.example.com/webhook/..."
                required
                data-testid="input-webhook-url"
              />
            </div>
            <div className="form-group">
              <Label className="mb-3 block">Eventos a escuchar *</Label>
              <div className="space-y-2">
                {WEBHOOK_EVENTS.map(event => (
                  <div key={event.value} className="flex items-center gap-2">
                    <Checkbox
                      id={event.value}
                      checked={formData.events.includes(event.value)}
                      onCheckedChange={() => toggleEvent(event.value)}
                      data-testid={`checkbox-${event.value}`}
                    />
                    <Label htmlFor={event.value} className="text-sm font-normal cursor-pointer">
                      {event.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="submit-create-webhook">
                Crear Webhook
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
