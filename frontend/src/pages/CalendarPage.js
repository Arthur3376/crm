import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  User,
  Phone,
  CheckCircle,
  XCircle,
  Calendar as CalendarIcon,
  ExternalLink,
  Link2,
  Unlink
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function CalendarPage() {
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [appointments, setAppointments] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [viewMode, setViewMode] = useState('month');
  const [googleCalendarStatus, setGoogleCalendarStatus] = useState({
    connected: false,
    email: null,
    configured: false
  });
  const [syncingAppointment, setSyncingAppointment] = useState(null);

  useEffect(() => {
    // Check for Google Calendar connection result
    const googleConnected = searchParams.get('google_connected');
    const error = searchParams.get('error');
    
    if (googleConnected === 'true') {
      toast.success('¡Google Calendar conectado exitosamente!');
      // Clear URL params
      window.history.replaceState({}, '', '/calendar');
    } else if (error) {
      toast.error('Error al conectar Google Calendar');
      window.history.replaceState({}, '', '/calendar');
    }
    
    fetchAppointments();
    fetchGoogleCalendarStatus();
    if (hasRole(['admin', 'gerente', 'supervisor'])) {
      fetchAgents();
    }
  }, [selectedAgent, searchParams]);

  const fetchAppointments = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedAgent && selectedAgent !== 'all') params.append('agent_id', selectedAgent);
      
      const response = await axios.get(`${API_URL}/api/appointments?${params}`, { withCredentials: true });
      setAppointments(response.data);
    } catch (error) {
      console.error('Error fetching appointments:', error);
      toast.error('Error al cargar las citas');
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

  const fetchGoogleCalendarStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/calendar/google/status`, { withCredentials: true });
      setGoogleCalendarStatus(response.data);
    } catch (error) {
      console.error('Error fetching Google Calendar status:', error);
    }
  };

  const handleConnectGoogleCalendar = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/google/calendar/login`, { withCredentials: true });
      window.location.href = response.data.authorization_url;
    } catch (error) {
      toast.error('Error al iniciar conexión con Google Calendar');
    }
  };

  const handleDisconnectGoogleCalendar = async () => {
    if (!window.confirm('¿Desconectar Google Calendar?')) return;
    
    try {
      await axios.post(`${API_URL}/api/calendar/google/disconnect`, {}, { withCredentials: true });
      toast.success('Google Calendar desconectado');
      setGoogleCalendarStatus({ connected: false, email: null, configured: true });
    } catch (error) {
      toast.error('Error al desconectar');
    }
  };

  const handleSyncToGoogle = async (appointmentId) => {
    setSyncingAppointment(appointmentId);
    try {
      const response = await axios.post(
        `${API_URL}/api/calendar/google/sync-appointment/${appointmentId}`,
        {},
        { withCredentials: true }
      );
      toast.success('Cita sincronizada con Google Calendar');
      fetchAppointments();
      
      // Open Google Calendar link if available
      if (response.data.event_link) {
        window.open(response.data.event_link, '_blank');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al sincronizar');
    } finally {
      setSyncingAppointment(null);
    }
  };

  const handleUpdateStatus = async (appointmentId, newStatus) => {
    try {
      await axios.put(`${API_URL}/api/appointments/${appointmentId}`, {
        status: newStatus
      }, { withCredentials: true });
      toast.success('Estado actualizado');
      fetchAppointments();
    } catch (error) {
      toast.error('Error al actualizar');
    }
  };

  const getAppointmentsForDate = (date) => {
    return appointments.filter(apt => {
      const aptDate = new Date(apt.scheduled_at);
      return aptDate.toDateString() === date.toDateString();
    });
  };

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    const days = [];
    
    for (let i = 0; i < startingDay; i++) {
      const prevDate = new Date(year, month, -startingDay + i + 1);
      days.push({ date: prevDate, isCurrentMonth: false });
    }
    
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({ date: new Date(year, month, i), isCurrentMonth: true });
    }
    
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      days.push({ date: new Date(year, month + 1, i), isCurrentMonth: false });
    }
    
    return days;
  };

  const navigateMonth = (direction) => {
    setSelectedDate(prev => {
      const newDate = new Date(prev);
      newDate.setMonth(newDate.getMonth() + direction);
      return newDate;
    });
  };

  const isToday = (date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const getStatusColor = (status) => {
    const colors = {
      pendiente: 'bg-amber-500',
      completada: 'bg-emerald-500',
      cancelada: 'bg-red-500'
    };
    return colors[status] || 'bg-slate-500';
  };

  const getStatusLabel = (status) => {
    const labels = {
      pendiente: 'Pendiente',
      completada: 'Completada',
      cancelada: 'Cancelada'
    };
    return labels[status] || status;
  };

  const days = getDaysInMonth(selectedDate);
  const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" data-testid="calendar-loading">
        <div className="h-12 bg-slate-200 rounded-md w-1/3" />
        <div className="h-96 bg-slate-200 rounded-md" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="calendar-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Calendario de Citas
          </h1>
          <p className="text-slate-500 mt-1">
            {appointments.length} cita{appointments.length !== 1 ? 's' : ''} programada{appointments.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Google Calendar Connection */}
          {googleCalendarStatus.configured && (
            googleCalendarStatus.connected ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-emerald-600 flex items-center gap-1">
                  <CheckCircle className="w-4 h-4" />
                  {googleCalendarStatus.email}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDisconnectGoogleCalendar}
                  className="text-red-600 border-red-200 hover:bg-red-50"
                >
                  <Unlink className="w-4 h-4 mr-1" />
                  Desconectar
                </Button>
              </div>
            ) : (
              <Button
                variant="outline"
                onClick={handleConnectGoogleCalendar}
                className="flex items-center gap-2"
                data-testid="connect-google-btn"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Conectar Google Calendar
              </Button>
            )
          )}
          
          {hasRole(['admin', 'gerente', 'supervisor']) && (
            <Select value={selectedAgent} onValueChange={setSelectedAgent}>
              <SelectTrigger className="w-48" data-testid="agent-filter">
                <SelectValue placeholder="Todos los agentes" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los agentes</SelectItem>
                {agents.map(a => (
                  <SelectItem key={a.user_id} value={a.user_id}>{a.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <div className="flex items-center border rounded-md">
            <Button
              variant={viewMode === 'month' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('month')}
              className={viewMode === 'month' ? 'bg-slate-900' : ''}
            >
              Mes
            </Button>
            <Button
              variant={viewMode === 'day' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('day')}
              className={viewMode === 'day' ? 'bg-slate-900' : ''}
            >
              Día
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Calendar */}
        <Card className="lg:col-span-3" data-testid="calendar-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigateMonth(-1)}>
                <ChevronLeft className="w-5 h-5" />
              </Button>
              <CardTitle className="text-xl font-semibold">
                {monthNames[selectedDate.getMonth()]} {selectedDate.getFullYear()}
              </CardTitle>
              <Button variant="ghost" size="icon" onClick={() => navigateMonth(1)}>
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>
            <Button variant="outline" size="sm" onClick={() => setSelectedDate(new Date())}>
              Hoy
            </Button>
          </CardHeader>
          <CardContent>
            {viewMode === 'month' ? (
              <div className="grid grid-cols-7 gap-px bg-slate-200 rounded-md overflow-hidden">
                {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map(day => (
                  <div key={day} className="bg-slate-50 p-2 text-center text-sm font-medium text-slate-500">
                    {day}
                  </div>
                ))}
                
                {days.map(({ date, isCurrentMonth }, index) => {
                  const dayAppointments = getAppointmentsForDate(date);
                  const isSelected = date.toDateString() === selectedDate.toDateString();
                  
                  return (
                    <div
                      key={index}
                      onClick={() => setSelectedDate(date)}
                      className={`
                        calendar-day bg-white cursor-pointer transition-colors
                        ${!isCurrentMonth ? 'opacity-40' : ''}
                        ${isToday(date) ? 'calendar-day-today' : ''}
                        ${isSelected ? 'ring-2 ring-slate-900 ring-inset' : ''}
                        hover:bg-slate-50
                      `}
                    >
                      <span className={`text-sm font-medium ${isToday(date) ? 'text-blue-600' : 'text-slate-900'}`}>
                        {date.getDate()}
                      </span>
                      <div className="mt-1 space-y-0.5 overflow-hidden">
                        {dayAppointments.slice(0, 2).map(apt => (
                          <div
                            key={apt.appointment_id}
                            className={`calendar-event text-white ${getStatusColor(apt.status)}`}
                            title={apt.title}
                          >
                            {apt.google_calendar_synced && <Link2 className="w-2 h-2 inline mr-0.5" />}
                            {apt.title}
                          </div>
                        ))}
                        {dayAppointments.length > 2 && (
                          <div className="text-xs text-slate-500 pl-1">
                            +{dayAppointments.length - 2} más
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-slate-900">
                  {selectedDate.toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </h3>
                {getAppointmentsForDate(selectedDate).length > 0 ? (
                  <div className="space-y-3">
                    {getAppointmentsForDate(selectedDate).map(apt => (
                      <div
                        key={apt.appointment_id}
                        className="p-4 border border-slate-200 rounded-md hover:border-slate-300 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-medium text-slate-900 flex items-center gap-2">
                              {apt.title}
                              {apt.google_calendar_synced && (
                                <span className="text-xs text-emerald-600 flex items-center gap-1">
                                  <Link2 className="w-3 h-3" />
                                  Sincronizado
                                </span>
                              )}
                            </h4>
                            <p className="text-sm text-slate-500 mt-1">{apt.description}</p>
                            <div className="flex items-center gap-4 mt-2 text-sm text-slate-600">
                              <span className="flex items-center gap-1">
                                <Clock className="w-4 h-4" />
                                {new Date(apt.scheduled_at).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                              </span>
                              <span className="flex items-center gap-1">
                                <User className="w-4 h-4" />
                                {apt.lead_name}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`pill-badge text-white ${getStatusColor(apt.status)}`}>
                              {getStatusLabel(apt.status)}
                            </span>
                            {apt.status === 'pendiente' && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleUpdateStatus(apt.appointment_id, 'completada')}
                                  className="text-emerald-600 hover:text-emerald-700"
                                >
                                  <CheckCircle className="w-5 h-5" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleUpdateStatus(apt.appointment_id, 'cancelada')}
                                  className="text-red-600 hover:text-red-700"
                                >
                                  <XCircle className="w-5 h-5" />
                                </Button>
                              </>
                            )}
                            {googleCalendarStatus.connected && !apt.google_calendar_synced && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleSyncToGoogle(apt.appointment_id)}
                                disabled={syncingAppointment === apt.appointment_id}
                              >
                                {syncingAppointment === apt.appointment_id ? (
                                  <div className="w-4 h-4 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
                                ) : (
                                  <>
                                    <CalendarIcon className="w-4 h-4 mr-1" />
                                    Sincronizar
                                  </>
                                )}
                              </Button>
                            )}
                            {apt.google_calendar_link && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => window.open(apt.google_calendar_link, '_blank')}
                                className="text-blue-600"
                              >
                                <ExternalLink className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">
                    <CalendarIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>No hay citas para este día</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sidebar */}
        <Card className="lg:col-span-1" data-testid="day-appointments">
          <CardHeader>
            <CardTitle className="text-lg">
              {selectedDate.toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric', month: 'short' })}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {getAppointmentsForDate(selectedDate).length > 0 ? (
              getAppointmentsForDate(selectedDate).map(apt => (
                <div
                  key={apt.appointment_id}
                  className="p-3 border border-slate-200 rounded-md hover:border-slate-300 cursor-pointer transition-colors"
                  onClick={() => navigate(`/leads/${apt.lead_id}`)}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`w-2 h-2 rounded-full ${getStatusColor(apt.status)}`} />
                    <span className="text-sm font-medium text-slate-900 flex-1 truncate">{apt.title}</span>
                    {apt.google_calendar_synced && <Link2 className="w-3 h-3 text-emerald-600" />}
                  </div>
                  <div className="text-xs text-slate-500 space-y-1">
                    <p className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(apt.scheduled_at).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    <p className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {apt.lead_name}
                    </p>
                    {apt.agent_name && (
                      <p className="flex items-center gap-1">
                        <Phone className="w-3 h-3" />
                        {apt.agent_name}
                      </p>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-400">
                <p className="text-sm">No hay citas</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
