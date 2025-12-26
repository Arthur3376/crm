import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
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
import { toast } from 'sonner';
import {
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  Mail,
  Phone,
  BookOpen,
  GraduationCap,
  X
} from 'lucide-react';
import { Avatar, AvatarFallback } from '../components/ui/avatar';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function TeachersPage() {
  const { user: currentUser } = useAuth();
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedTeacher, setSelectedTeacher] = useState(null);
  const [newSubject, setNewSubject] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subjects: []
  });

  useEffect(() => {
    fetchTeachers();
  }, []);

  const fetchTeachers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/teachers`, { withCredentials: true });
      setTeachers(response.data);
    } catch (error) {
      console.error('Error fetching teachers:', error);
      toast.error('Error al cargar los maestros');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTeacher = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/teachers`, formData, { withCredentials: true });
      toast.success('Maestro creado exitosamente');
      setShowCreateModal(false);
      resetForm();
      fetchTeachers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear el maestro');
    }
  };

  const handleUpdateTeacher = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API_URL}/api/teachers/${selectedTeacher.teacher_id}`, formData, { withCredentials: true });
      toast.success('Maestro actualizado');
      setShowEditModal(false);
      setSelectedTeacher(null);
      fetchTeachers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar');
    }
  };

  const handleDeleteTeacher = async (teacherId) => {
    if (!window.confirm('¿Estás seguro de eliminar este maestro?')) return;
    try {
      await axios.delete(`${API_URL}/api/teachers/${teacherId}`, { withCredentials: true });
      toast.success('Maestro eliminado');
      fetchTeachers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  const openEditModal = (teacher) => {
    setSelectedTeacher(teacher);
    setFormData({
      name: teacher.name,
      email: teacher.email,
      phone: teacher.phone || '',
      subjects: teacher.subjects || []
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      phone: '',
      subjects: []
    });
    setNewSubject('');
  };

  const addSubject = () => {
    if (newSubject.trim() && !formData.subjects.includes(newSubject.trim())) {
      setFormData(prev => ({
        ...prev,
        subjects: [...prev.subjects, newSubject.trim()]
      }));
      setNewSubject('');
    }
  };

  const removeSubject = (subject) => {
    setFormData(prev => ({
      ...prev,
      subjects: prev.subjects.filter(s => s !== subject)
    }));
  };

  const getInitials = (name) => {
    if (!name) return 'M';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
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
            Maestros
          </h1>
          <p className="text-slate-500 mt-1">
            {teachers.length} maestro{teachers.length !== 1 ? 's' : ''} registrado{teachers.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button
          onClick={() => { resetForm(); setShowCreateModal(true); }}
          className="bg-slate-900 hover:bg-slate-800 text-white"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Maestro
        </Button>
      </div>

      {/* Info Card */}
      <Card className="bg-purple-50 border-purple-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <GraduationCap className="w-5 h-5 text-purple-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-purple-900">Gestión de Maestros</h3>
              <p className="text-sm text-purple-700 mt-1">
                Los maestros pueden ser asignados a las materias de cada carrera. Registra sus datos de contacto y las materias que imparten.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Teachers Table */}
      <Card>
        <CardContent className="p-0">
          {teachers.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead className="font-medium">Maestro</TableHead>
                    <TableHead className="font-medium">Contacto</TableHead>
                    <TableHead className="font-medium">Materias</TableHead>
                    <TableHead className="font-medium">Registrado</TableHead>
                    <TableHead className="text-right font-medium">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {teachers.map((teacher) => (
                    <TableRow key={teacher.teacher_id} className="table-row-hover">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-9 w-9">
                            <AvatarFallback className="bg-purple-100 text-purple-600 text-sm">
                              {getInitials(teacher.name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium text-slate-900">{teacher.name}</p>
                            <p className="text-xs text-slate-500">{teacher.teacher_id}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <span className="text-sm text-slate-600 flex items-center gap-1">
                            <Mail className="w-3 h-3" />
                            {teacher.email}
                          </span>
                          {teacher.phone && (
                            <span className="text-sm text-slate-600 flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              {teacher.phone}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {teacher.subjects?.length > 0 ? (
                          <div className="flex flex-wrap gap-1 max-w-[250px]">
                            {teacher.subjects.map(subject => (
                              <span key={subject} className="pill-badge bg-purple-100 text-purple-700 border-purple-200 border text-xs">
                                {subject}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">Sin materias asignadas</span>
                        )}
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm">
                        {new Date(teacher.created_at).toLocaleDateString('es-ES')}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditModal(teacher)}>
                              <Pencil className="w-4 h-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            {currentUser?.role === 'admin' && (
                              <DropdownMenuItem
                                onClick={() => handleDeleteTeacher(teacher.teacher_id)}
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Eliminar
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="empty-state py-16">
              <GraduationCap className="empty-state-icon" />
              <h3 className="text-lg font-medium text-slate-900 mb-1">No hay maestros</h3>
              <p className="text-slate-500 mb-4">Comienza registrando al primer maestro</p>
              <Button onClick={() => { resetForm(); setShowCreateModal(true); }}>
                <Plus className="w-4 h-4 mr-2" />
                Nuevo Maestro
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Teacher Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Nuevo Maestro</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTeacher} className="space-y-4">
            <div className="form-group">
              <Label htmlFor="name">Nombre completo *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <Label htmlFor="email">Correo electrónico *</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <Label htmlFor="phone">Teléfono</Label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <Label className="flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                Materias que imparte
              </Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Nombre de la materia"
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSubject())}
                />
                <Button type="button" onClick={addSubject} variant="outline">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              {formData.subjects.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {formData.subjects.map(subject => (
                    <span key={subject} className="pill-badge bg-purple-100 text-purple-700 border-purple-200 border text-xs flex items-center gap-1">
                      {subject}
                      <button type="button" onClick={() => removeSubject(subject)} className="hover:text-purple-900">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800">
                Crear Maestro
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Teacher Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Editar Maestro</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateTeacher} className="space-y-4">
            <div className="form-group">
              <Label htmlFor="edit-name">Nombre completo *</Label>
              <Input
                id="edit-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <Label htmlFor="edit-email">Correo electrónico *</Label>
              <Input
                id="edit-email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <Label htmlFor="edit-phone">Teléfono</Label>
              <Input
                id="edit-phone"
                value={formData.phone}
                onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <Label className="flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                Materias que imparte
              </Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Nombre de la materia"
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSubject())}
                />
                <Button type="button" onClick={addSubject} variant="outline">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              {formData.subjects.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {formData.subjects.map(subject => (
                    <span key={subject} className="pill-badge bg-purple-100 text-purple-700 border-purple-200 border text-xs flex items-center gap-1">
                      {subject}
                      <button type="button" onClick={() => removeSubject(subject)} className="hover:text-purple-900">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowEditModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800">
                Guardar Cambios
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
