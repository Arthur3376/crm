import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import {
  ArrowLeft,
  Phone,
  Mail,
  Calendar,
  User,
  MessageSquare,
  Send,
  Edit2,
  Save,
  X,
  Clock,
  ExternalLink,
  Facebook,
  Instagram,
  Music2,
  PenLine,
  GraduationCap
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SOURCE_ICONS = {
  facebook: Facebook,
  instagram: Instagram,
  tiktok: Music2,
  manual: PenLine
};

const STATUSES = [
  { value: 'etapa_1_informacion', label: 'Etapa 1 - Información', color: 'bg-blue-100 text-blue-700' },
  { value: 'etapa_2_contacto', label: 'Etapa 2 - Contacto', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'etapa_3_documentacion', label: 'Etapa 3 - Documentación', color: 'bg-purple-100 text-purple-700' },
  { value: 'etapa_4_inscrito', label: 'Etapa 4 - Inscrito', color: 'bg-green-100 text-green-700' },
];

const CAREERS = [
  'Ingeniería', 'Medicina', 'Derecho', 'Administración',
  'Contabilidad', 'Psicología', 'Diseño', 'Marketing', 'Otra'
];

export default function LeadDetailPage() {
  const { leadId } = useParams();
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  
  const [lead, setLead] = useState(null);
  const [conversation, setConversation] = useState(null);
  const [agents, setAgents] = useState([]);
  const [careers, setCareers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [newMessage, setNewMessage] = useState('');
  const [showAppointmentModal, setShowAppointmentModal] = useState(false);
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [convertData, setConvertData] = useState({
    career_id: '',
    career_name: '',
    institutional_email: ''
  });
  const [appointmentData, setAppointmentData] = useState({
    title: '',
    description: '',
    scheduled_at: ''
  });

  useEffect(() => {
    fetchLeadData();
    if (hasRole(['admin', 'gerente', 'supervisor'])) {
      fetchAgents();
    }
    fetchCareers();
  }, [leadId]);

  const fetchCareers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/careers/full`, { withCredentials: true });
      setCareers(response.data);
    } catch (error) {
      console.error('Error fetching careers:', error);
    }
  };

  const fetchLeadData = async () => {
    try {
      const [leadRes, convRes] = await Promise.all([
        axios.get(`${API_URL}/api/leads/${leadId}`, { withCredentials: true }),
        axios.get(`${API_URL}/api/leads/${leadId}/conversations`, { withCredentials: true })
      ]);
      setLead(leadRes.data);
      setConversation(convRes.data);
      setEditData(leadRes.data);
    } catch (error) {
      console.error('Error fetching lead:', error);
      toast.error('Error al cargar el lead');
      navigate('/leads');
    } finally {
      setLoading(false);
    }
  };

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/users/agents`, { withCredentials: true });
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const handleSaveChanges = async () => {
    try {
      const updateData = {
        full_name: editData.full_name,
        email: editData.email,
        phone: editData.phone,
        career_interest: editData.career_interest,
        status: editData.status,
        notes: editData.notes,
        assigned_agent_id: editData.assigned_agent_id
      };
      
      await axios.put(`${API_URL}/api/leads/${leadId}`, updateData, { withCredentials: true });
      toast.success('Lead actualizado');
      setEditing(false);
      fetchLeadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      await axios.post(`${API_URL}/api/conversations`, {
        lead_id: leadId,
        message: newMessage,
        sender: 'agent'
      }, { withCredentials: true });
      
      setNewMessage('');
      fetchLeadData();
    } catch (error) {
      toast.error('Error al enviar mensaje');
    }
  };

  const handleCreateAppointment = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/appointments`, {
        lead_id: leadId,
        agent_id: lead.assigned_agent_id || user.user_id,
        title: appointmentData.title,
        description: appointmentData.description,
        scheduled_at: new Date(appointmentData.scheduled_at).toISOString()
      }, { withCredentials: true });
      
      toast.success('Cita agendada');
      setShowAppointmentModal(false);
      setAppointmentData({ title: '', description: '', scheduled_at: '' });
      fetchLeadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al agendar cita');
    }
  };

  const handleConvertToStudent = async (e) => {
    e.preventDefault();
    if (!convertData.career_id) {
      toast.error('Selecciona una carrera');
      return;
    }

    try {
      await axios.post(`${API_URL}/api/leads/${leadId}/convert-to-student`, convertData, { withCredentials: true });
      toast.success('Lead convertido a estudiante exitosamente');
      setShowConvertModal(false);
      navigate('/students');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al convertir');
    }
  };

  const getStatusLabel = (status) => {
    const item = STATUSES.find(s => s.value === status);
    return item?.label || status;
  };

  const SourceIcon = SOURCE_ICONS[lead?.source] || PenLine;

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" data-testid="lead-detail-loading">
        <div className="h-8 bg-slate-200 rounded w-1/4" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-96 bg-slate-200 rounded-md" />
          <div className="h-96 bg-slate-200 rounded-md" />
        </div>
      </div>
    );
  }

  if (!lead) return null;

  return (
    <div className="space-y-6" data-testid="lead-detail-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/leads')}
            data-testid="back-btn"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {lead.full_name}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={`pill-badge status-${lead.status} border`}>
                {getStatusLabel(lead.status)}
              </span>
              <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium source-${lead.source}`}>
                <SourceIcon className="w-3 h-3" />
                <span className="capitalize">{lead.source}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {lead.status === 'etapa_4_inscrito' && !lead.converted_to_student && hasRole(['admin', 'gerente']) && (
            <Button
              onClick={() => {
                const matchingCareer = careers.find(c => c.name === lead.career_interest);
                setConvertData({
                  career_id: matchingCareer?.career_id || '',
                  career_name: matchingCareer?.name || lead.career_interest,
                  institutional_email: ''
                });
                setShowConvertModal(true);
              }}
              className="bg-green-600 hover:bg-green-700"
            >
              <GraduationCap className="w-4 h-4 mr-2" />
              Convertir a Estudiante
            </Button>
          )}
          {lead.converted_to_student && (
            <span className="pill-badge bg-green-100 text-green-700 border-green-200 border">
              ✓ Convertido a Estudiante
            </span>
          )}
          <Button
            variant="outline"
            onClick={() => setShowAppointmentModal(true)}
            data-testid="schedule-appointment-btn"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Agendar Cita
          </Button>
          {!editing ? (
            <Button onClick={() => setEditing(true)} data-testid="edit-btn">
              <Edit2 className="w-4 h-4 mr-2" />
              Editar
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => { setEditing(false); setEditData(lead); }}>
                <X className="w-4 h-4 mr-2" />
                Cancelar
              </Button>
              <Button onClick={handleSaveChanges} className="bg-emerald-600 hover:bg-emerald-700" data-testid="save-btn">
                <Save className="w-4 h-4 mr-2" />
                Guardar
              </Button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lead Info */}
        <div className="lg:col-span-2 space-y-6">
          <Card data-testid="lead-info-card">
            <CardHeader>
              <CardTitle className="text-lg">Información del Lead</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-group">
                  <Label className="text-slate-500">Nombre completo</Label>
                  {editing ? (
                    <Input
                      value={editData.full_name}
                      onChange={(e) => setEditData(prev => ({ ...prev, full_name: e.target.value }))}
                    />
                  ) : (
                    <p className="text-slate-900 font-medium">{lead.full_name}</p>
                  )}
                </div>
                <div className="form-group">
                  <Label className="text-slate-500">Correo electrónico</Label>
                  {editing ? (
                    <Input
                      type="email"
                      value={editData.email}
                      onChange={(e) => setEditData(prev => ({ ...prev, email: e.target.value }))}
                    />
                  ) : (
                    <a href={`mailto:${lead.email}`} className="text-blue-600 hover:underline flex items-center gap-1">
                      <Mail className="w-4 h-4" />
                      {lead.email}
                    </a>
                  )}
                </div>
                <div className="form-group">
                  <Label className="text-slate-500">Teléfono</Label>
                  {editing ? (
                    <Input
                      value={editData.phone}
                      onChange={(e) => setEditData(prev => ({ ...prev, phone: e.target.value }))}
                    />
                  ) : (
                    <div className="flex items-center gap-2">
                      <span className="text-slate-900">{lead.phone}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(lead.phone).then(() => {
                            toast.success(`Número copiado: ${lead.phone}`);
                          }).catch(() => {
                            toast.error('Error al copiar el número');
                          });
                        }}
                        className="text-green-600 hover:text-green-700 h-8 px-2"
                      >
                        <Phone className="w-4 h-4 mr-1" />
                        Copiar
                      </Button>
                    </div>
                  )}
                </div>
                <div className="form-group">
                  <Label className="text-slate-500">Carrera de interés</Label>
                  {editing ? (
                    <Select
                      value={editData.career_interest}
                      onValueChange={(value) => setEditData(prev => ({ ...prev, career_interest: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CAREERS.map(c => (
                          <SelectItem key={c} value={c}>{c}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <p className="text-slate-900">{lead.career_interest}</p>
                  )}
                </div>
                <div className="form-group">
                  <Label className="text-slate-500">Estado</Label>
                  {editing ? (
                    <Select
                      value={editData.status}
                      onValueChange={(value) => setEditData(prev => ({ ...prev, status: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {STATUSES.map(s => (
                          <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <span className={`pill-badge status-${lead.status} border`}>
                      {getStatusLabel(lead.status)}
                    </span>
                  )}
                </div>
                {hasRole(['admin', 'gerente', 'supervisor']) && (
                  <div className="form-group">
                    <Label className="text-slate-500">Agente asignado</Label>
                    {editing ? (
                      <Select
                        value={editData.assigned_agent_id || ''}
                        onValueChange={(value) => setEditData(prev => ({ ...prev, assigned_agent_id: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Sin asignar" />
                        </SelectTrigger>
                        <SelectContent>
                          {agents.map(a => (
                            <SelectItem key={a.user_id} value={a.user_id}>{a.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <p className="text-slate-900 flex items-center gap-1">
                        <User className="w-4 h-4" />
                        {lead.assigned_agent_name || 'Sin asignar'}
                      </p>
                    )}
                  </div>
                )}
              </div>
              
              <div className="form-group">
                <Label className="text-slate-500">Notas</Label>
                {editing ? (
                  <Textarea
                    value={editData.notes || ''}
                    onChange={(e) => setEditData(prev => ({ ...prev, notes: e.target.value }))}
                    placeholder="Agregar notas sobre el lead..."
                    rows={4}
                  />
                ) : (
                  <p className="text-slate-700 whitespace-pre-wrap">
                    {lead.notes || 'Sin notas'}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-4 text-sm text-slate-500 pt-4 border-t">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  Creado: {new Date(lead.created_at).toLocaleString('es-ES')}
                </span>
                <span>
                  Actualizado: {new Date(lead.updated_at).toLocaleString('es-ES')}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Conversation History */}
        <div className="lg:col-span-1">
          <Card className="h-[600px] flex flex-col" data-testid="conversation-card">
            <CardHeader className="border-b">
              <CardTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Historial de Conversación
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-3">
              {conversation?.messages?.length > 0 ? (
                conversation.messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`chat-bubble ${msg.sender === 'agent' ? 'chat-bubble-agent' : 'chat-bubble-lead'}`}
                  >
                    <p className="text-sm">{msg.message}</p>
                    <p className={`text-xs mt-1 ${msg.sender === 'agent' ? 'text-slate-300' : 'text-slate-500'}`}>
                      {new Date(msg.timestamp).toLocaleString('es-ES')}
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-center text-slate-400 py-8">
                  <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No hay mensajes</p>
                </div>
              )}
            </CardContent>
            <div className="p-4 border-t">
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Input
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Escribir nota..."
                  className="flex-1"
                  data-testid="message-input"
                />
                <Button type="submit" size="icon" data-testid="send-message-btn">
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </Card>
        </div>
      </div>

      {/* Appointment Modal */}
      <Dialog open={showAppointmentModal} onOpenChange={setShowAppointmentModal}>
        <DialogContent className="sm:max-w-md" data-testid="appointment-modal">
          <DialogHeader>
            <DialogTitle>Agendar Cita</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateAppointment} className="space-y-4">
            <div className="form-group">
              <Label htmlFor="title">Título *</Label>
              <Input
                id="title"
                value={appointmentData.title}
                onChange={(e) => setAppointmentData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Ej: Llamada de seguimiento"
                required
                data-testid="appointment-title"
              />
            </div>
            <div className="form-group">
              <Label htmlFor="scheduled_at">Fecha y hora *</Label>
              <Input
                id="scheduled_at"
                type="datetime-local"
                value={appointmentData.scheduled_at}
                onChange={(e) => setAppointmentData(prev => ({ ...prev, scheduled_at: e.target.value }))}
                required
                data-testid="appointment-datetime"
              />
            </div>
            <div className="form-group">
              <Label htmlFor="description">Descripción</Label>
              <Textarea
                id="description"
                value={appointmentData.description}
                onChange={(e) => setAppointmentData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Notas adicionales..."
                rows={3}
                data-testid="appointment-description"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowAppointmentModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="submit-appointment">
                Agendar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Convert to Student Modal */}
      <Dialog open={showConvertModal} onOpenChange={setShowConvertModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GraduationCap className="w-5 h-5" />
              Convertir a Estudiante
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleConvertToStudent} className="space-y-4">
            <div className="p-3 bg-green-50 rounded-md">
              <p className="text-sm text-green-800">
                <strong>{lead?.full_name}</strong> será registrado como estudiante con acceso a:
              </p>
              <ul className="text-xs text-green-700 mt-2 list-disc list-inside">
                <li>Carpeta de documentos personal</li>
                <li>Horario de clases asignado</li>
                <li>Registro de asistencia</li>
                <li>Email institucional</li>
              </ul>
            </div>
            <div className="form-group">
              <Label>Carrera *</Label>
              <Select
                value={convertData.career_id}
                onValueChange={(value) => {
                  const career = careers.find(c => c.career_id === value);
                  setConvertData(prev => ({
                    ...prev,
                    career_id: value,
                    career_name: career?.name || ''
                  }));
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar carrera" />
                </SelectTrigger>
                <SelectContent>
                  {careers.map(career => (
                    <SelectItem key={career.career_id} value={career.career_id}>
                      {career.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="form-group">
              <Label>Email Institucional</Label>
              <Input
                type="email"
                value={convertData.institutional_email}
                onChange={(e) => setConvertData(prev => ({ ...prev, institutional_email: e.target.value }))}
                placeholder="estudiante@tudominio.edu"
              />
              <p className="text-xs text-slate-500 mt-1">
                Asigna el correo de tu dominio (Google Workspace)
              </p>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowConvertModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-green-600 hover:bg-green-700">
                <GraduationCap className="w-4 h-4 mr-1" />
                Convertir
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
