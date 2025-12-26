import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Calendar as CalendarComponent } from '../components/ui/calendar';
import { toast } from 'sonner';
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  User,
  Phone,
  CheckCircle,
  XCircle,
  Calendar as CalendarIcon
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function CalendarPage() {
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [viewMode, setViewMode] = useState('month'); // 'month' or 'day'

  useEffect(() => {
    fetchAppointments();
    if (hasRole(['admin', 'gerente', 'supervisor'])) {
      fetchAgents();
    }
  }, [selectedAgent]);

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
    
    // Previous month days
    for (let i = 0; i < startingDay; i++) {
      const prevDate = new Date(year, month, -startingDay + i + 1);
      days.push({ date: prevDate, isCurrentMonth: false });
    }
    
    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({ date: new Date(year, month, i), isCurrentMonth: true });
    }
    
    // Next month days
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
        <div className="flex items-center gap-3">
          {hasRole(['admin', 'gerente', 'supervisor']) && (
            <Select
              value={selectedAgent}
              onValueChange={setSelectedAgent}
            >
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
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedDate(new Date())}
            >
              Hoy
            </Button>
          </CardHeader>
          <CardContent>
            {viewMode === 'month' ? (
              <div className="grid grid-cols-7 gap-px bg-slate-200 rounded-md overflow-hidden">
                {/* Day headers */}
                {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map(day => (
                  <div key={day} className="bg-slate-50 p-2 text-center text-sm font-medium text-slate-500">
                    {day}
                  </div>
                ))}
                
                {/* Calendar days */}
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
                            <h4 className="font-medium text-slate-900">{apt.title}</h4>
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

        {/* Sidebar - Selected day appointments */}
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
                    <span className="text-sm font-medium text-slate-900">{apt.title}</span>
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
