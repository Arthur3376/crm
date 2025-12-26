import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from '../components/ui/card';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../components/ui/accordion';
import { toast } from 'sonner';
import {
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  GraduationCap,
  Clock,
  MapPin,
  Monitor,
  Building,
  Calendar,
  X
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DAYS = [
  { value: 'lunes', label: 'Lunes' },
  { value: 'martes', label: 'Martes' },
  { value: 'miercoles', label: 'Miércoles' },
  { value: 'jueves', label: 'Jueves' },
  { value: 'viernes', label: 'Viernes' },
  { value: 'sabado', label: 'Sábado' },
  { value: 'domingo', label: 'Domingo' },
];

const MODALITIES = [
  { value: 'presencial', label: 'Presencial' },
  { value: 'online', label: 'En Línea' },
  { value: 'hibrido', label: 'Híbrido' },
];

export default function CareersPage() {
  const { user: currentUser } = useAuth();
  const [careers, setCareers] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedCareer, setSelectedCareer] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    modality: 'presencial',
    schedules: []
  });
  const [scheduleForm, setScheduleForm] = useState({
    subject: '',
    teacher_id: '',
    day: 'lunes',
    start_time: '08:00',
    end_time: '10:00',
    mode: 'presencial',
    classroom: ''
  });

  useEffect(() => {
    fetchCareers();
    fetchTeachers();
  }, []);

  const fetchCareers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/careers/full`, { withCredentials: true });
      setCareers(response.data);
    } catch (error) {
      console.error('Error fetching careers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeachers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/teachers`, { withCredentials: true });
      setTeachers(response.data);
    } catch (error) {
      console.error('Error fetching teachers:', error);
    }
  };

  const handleCreateCareer = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/careers/full`, formData, { withCredentials: true });
      toast.success('Carrera creada exitosamente');
      setShowCreateModal(false);
      resetForm();
      fetchCareers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear la carrera');
    }
  };

  const handleUpdateCareer = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API_URL}/api/careers/full/${selectedCareer.career_id}`, formData, { withCredentials: true });
      toast.success('Carrera actualizada');
      setShowEditModal(false);
      setSelectedCareer(null);
      fetchCareers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar');
    }
  };

  const handleDeleteCareer = async (careerId) => {
    if (!window.confirm('¿Estás seguro de eliminar esta carrera y sus horarios?')) return;
    try {
      await axios.delete(`${API_URL}/api/careers/full/${careerId}`, { withCredentials: true });
      toast.success('Carrera eliminada');
      fetchCareers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  const openEditModal = (career) => {
    setSelectedCareer(career);
    setFormData({
      name: career.name,
      description: career.description || '',
      modality: career.modality,
      schedules: career.schedules || []
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      modality: 'presencial',
      schedules: []
    });
  };

  const resetScheduleForm = () => {
    setScheduleForm({
      subject: '',
      teacher_id: '',
      day: 'lunes',
      start_time: '08:00',
      end_time: '10:00',
      mode: 'presencial',
      classroom: ''
    });
  };

  const addSchedule = () => {
    if (!scheduleForm.subject.trim()) {
      toast.error('Ingresa el nombre de la materia');
      return;
    }
    
    const teacher = teachers.find(t => t.teacher_id === scheduleForm.teacher_id);
    const newSchedule = {
      ...scheduleForm,
      teacher_name: teacher ? teacher.name : null
    };
    
    setFormData(prev => ({
      ...prev,
      schedules: [...prev.schedules, newSchedule]
    }));
    
    resetScheduleForm();
    setShowScheduleModal(false);
    toast.success('Horario agregado');
  };

  const removeSchedule = (index) => {
    setFormData(prev => ({
      ...prev,
      schedules: prev.schedules.filter((_, i) => i !== index)
    }));
  };

  const getModalityBadge = (modality) => {
    const badges = {
      presencial: 'bg-green-100 text-green-700 border-green-200',
      online: 'bg-blue-100 text-blue-700 border-blue-200',
      hibrido: 'bg-purple-100 text-purple-700 border-purple-200'
    };
    const labels = {
      presencial: 'Presencial',
      online: 'En Línea',
      hibrido: 'Híbrido'
    };
    return (
      <span className={`pill-badge ${badges[modality]} border text-xs`}>
        {labels[modality]}
      </span>
    );
  };

  const getDayLabel = (day) => {
    const item = DAYS.find(d => d.value === day);
    return item ? item.label : day;
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-12 bg-slate-200 rounded-md w-1/3" />
        <div className="h-96 bg-slate-200 rounded-md" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Carreras y Horarios
          </h1>
          <p className="text-slate-500 mt-1">
            {careers.length} carrera{careers.length !== 1 ? 's' : ''} con horarios configurados
          </p>
        </div>
        <Button
          onClick={() => { resetForm(); setShowCreateModal(true); }}
          className="bg-slate-900 hover:bg-slate-800 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nueva Carrera
        </Button>
      </div>

      {/* Info Card */}
      <Card className="bg-amber-50 border-amber-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-amber-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-900">Gestión de Carreras y Horarios</h3>
              <p className="text-sm text-amber-700 mt-1">
                Configura las carreras con sus horarios de clases (presenciales y en línea). 
                Asigna maestros a cada materia para generar el horario completo de cada carrera.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Careers List */}
      {careers.length > 0 ? (
        <div className="space-y-4">
          {careers.map((career) => (
            <Card key={career.career_id}>
              <CardContent className="p-0">
                <div className="p-4 border-b flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-slate-900 rounded-lg flex items-center justify-center">
                      <GraduationCap className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{career.name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        {getModalityBadge(career.modality)}
                        <span className="text-xs text-slate-500">
                          {career.schedules?.length || 0} horarios
                        </span>
                      </div>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => openEditModal(career)}>
                        <Pencil className="w-4 h-4 mr-2" />
                        Editar
                      </DropdownMenuItem>
                      {currentUser?.role === 'admin' && (
                        <DropdownMenuItem
                          onClick={() => handleDeleteCareer(career.career_id)}
                          className="text-red-600"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Eliminar
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                
                {career.description && (
                  <p className="px-4 py-2 text-sm text-slate-600 border-b">{career.description}</p>
                )}
                
                {career.schedules?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-slate-50">
                          <TableHead className="font-medium">Materia</TableHead>
                          <TableHead className="font-medium">Maestro</TableHead>
                          <TableHead className="font-medium">Día</TableHead>
                          <TableHead className="font-medium">Horario</TableHead>
                          <TableHead className="font-medium">Modalidad</TableHead>
                          <TableHead className="font-medium">Aula/Link</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {career.schedules.map((schedule, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">{schedule.subject}</TableCell>
                            <TableCell>{schedule.teacher_name || '-'}</TableCell>
                            <TableCell>{getDayLabel(schedule.day)}</TableCell>
                            <TableCell>
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {schedule.start_time} - {schedule.end_time}
                              </span>
                            </TableCell>
                            <TableCell>
                              <span className={`pill-badge text-xs ${
                                schedule.mode === 'presencial' 
                                  ? 'bg-green-100 text-green-700' 
                                  : 'bg-blue-100 text-blue-700'
                              }`}>
                                {schedule.mode === 'presencial' ? (
                                  <><Building className="w-3 h-3 mr-1 inline" />Presencial</>
                                ) : (
                                  <><Monitor className="w-3 h-3 mr-1 inline" />En Línea</>
                                )}
                              </span>
                            </TableCell>
                            <TableCell className="text-slate-600 text-sm">
                              {schedule.classroom || '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="p-6 text-center text-slate-500">
                    <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No hay horarios configurados</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-16">
            <div className="empty-state">
              <GraduationCap className="empty-state-icon" />
              <h3 className="text-lg font-medium text-slate-900 mb-1">No hay carreras</h3>
              <p className="text-slate-500 mb-4">Comienza creando la primera carrera con sus horarios</p>
              <Button onClick={() => { resetForm(); setShowCreateModal(true); }}>
                <Plus className="w-4 h-4 mr-2" />
                Nueva Carrera
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create/Edit Career Modal */}
      <Dialog open={showCreateModal || showEditModal} onOpenChange={(open) => {
        if (!open) {
          setShowCreateModal(false);
          setShowEditModal(false);
          setSelectedCareer(null);
        }
      }}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{showEditModal ? 'Editar Carrera' : 'Nueva Carrera'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={showEditModal ? handleUpdateCareer : handleCreateCareer} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="form-group">
                <Label htmlFor="name">Nombre de la carrera *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  required
                  placeholder="Ej: Ingeniería en Sistemas"
                />
              </div>
              <div className="form-group">
                <Label>Modalidad *</Label>
                <Select
                  value={formData.modality}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, modality: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {MODALITIES.map(m => (
                      <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="form-group">
              <Label htmlFor="description">Descripción</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Descripción de la carrera..."
                rows={2}
              />
            </div>

            {/* Schedules Section */}
            <div className="border rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Horarios de Clases
                </Label>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowScheduleModal(true)}>
                  <Plus className="w-4 h-4 mr-1" />
                  Agregar Horario
                </Button>
              </div>
              
              {formData.schedules.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {formData.schedules.map((schedule, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-slate-50 rounded-md text-sm">
                      <div className="flex items-center gap-4">
                        <span className="font-medium">{schedule.subject}</span>
                        <span className="text-slate-500">{getDayLabel(schedule.day)}</span>
                        <span className="text-slate-500">{schedule.start_time} - {schedule.end_time}</span>
                        <span className={`pill-badge text-xs ${schedule.mode === 'presencial' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                          {schedule.mode}
                        </span>
                      </div>
                      <Button type="button" variant="ghost" size="sm" onClick={() => removeSchedule(idx)} className="text-red-600 h-6 w-6 p-0">
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 text-center py-4">No hay horarios agregados</p>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => { setShowCreateModal(false); setShowEditModal(false); }}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800">
                {showEditModal ? 'Guardar Cambios' : 'Crear Carrera'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add Schedule Modal */}
      <Dialog open={showScheduleModal} onOpenChange={setShowScheduleModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Agregar Horario</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="form-group">
              <Label>Materia *</Label>
              <Input
                value={scheduleForm.subject}
                onChange={(e) => setScheduleForm(prev => ({ ...prev, subject: e.target.value }))}
                placeholder="Nombre de la materia"
              />
            </div>
            
            <div className="form-group">
              <Label>Maestro</Label>
              <Select
                value={scheduleForm.teacher_id || "none"}
                onValueChange={(value) => setScheduleForm(prev => ({ ...prev, teacher_id: value === "none" ? "" : value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar maestro (opcional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Sin asignar</SelectItem>
                  {teachers.map(t => (
                    <SelectItem key={t.teacher_id} value={t.teacher_id}>{t.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="form-group">
                <Label>Día *</Label>
                <Select
                  value={scheduleForm.day}
                  onValueChange={(value) => setScheduleForm(prev => ({ ...prev, day: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DAYS.map(d => (
                      <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="form-group">
                <Label>Modalidad *</Label>
                <Select
                  value={scheduleForm.mode}
                  onValueChange={(value) => setScheduleForm(prev => ({ ...prev, mode: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="presencial">Presencial</SelectItem>
                    <SelectItem value="online">En Línea</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="form-group">
                <Label>Hora Inicio *</Label>
                <Input
                  type="time"
                  value={scheduleForm.start_time}
                  onChange={(e) => setScheduleForm(prev => ({ ...prev, start_time: e.target.value }))}
                />
              </div>
              <div className="form-group">
                <Label>Hora Fin *</Label>
                <Input
                  type="time"
                  value={scheduleForm.end_time}
                  onChange={(e) => setScheduleForm(prev => ({ ...prev, end_time: e.target.value }))}
                />
              </div>
            </div>
            
            <div className="form-group">
              <Label>{scheduleForm.mode === 'presencial' ? 'Aula' : 'Link de Clase'}</Label>
              <Input
                value={scheduleForm.classroom}
                onChange={(e) => setScheduleForm(prev => ({ ...prev, classroom: e.target.value }))}
                placeholder={scheduleForm.mode === 'presencial' ? 'Ej: Aula 101' : 'Ej: https://zoom.us/...'}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setShowScheduleModal(false)}>
              Cancelar
            </Button>
            <Button onClick={addSchedule} className="bg-slate-900 hover:bg-slate-800">
              Agregar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
