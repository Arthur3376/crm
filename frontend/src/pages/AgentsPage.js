import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
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
import { toast } from 'sonner';
import {
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  UserCircle,
  Mail,
  Phone,
  GraduationCap,
  Key,
  Users
} from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CAREERS = [
  'Ingeniería', 'Medicina', 'Derecho', 'Administración',
  'Contabilidad', 'Psicología', 'Diseño', 'Marketing', 'Otra'
];

export default function AgentsPage() {
  const { user: currentUser } = useAuth();
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    assigned_careers: []
  });
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/users`, { withCredentials: true });
      // Filter only agents
      const agentsOnly = response.data.filter(u => u.role === 'agente');
      setAgents(agentsOnly);
    } catch (error) {
      console.error('Error fetching agents:', error);
      toast.error('Error al cargar los agentes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAgent = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/auth/register`, {
        ...formData,
        role: 'agente'
      }, { withCredentials: true });
      toast.success('Agente creado exitosamente');
      setShowCreateModal(false);
      resetForm();
      fetchAgents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear el agente');
    }
  };

  const handleUpdateAgent = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API_URL}/api/users/${selectedAgent.user_id}`, {
        name: formData.name,
        phone: formData.phone,
        is_active: formData.is_active,
        assigned_careers: formData.assigned_careers
      }, { withCredentials: true });
      toast.success('Agente actualizado');
      setShowEditModal(false);
      setSelectedAgent(null);
      fetchAgents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar');
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/users/${selectedAgent.user_id}/reset-password`, {
        new_password: newPassword
      }, { withCredentials: true });
      toast.success('Contraseña actualizada exitosamente');
      setShowResetPasswordModal(false);
      setSelectedAgent(null);
      setNewPassword('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al resetear contraseña');
    }
  };

  const handleDeleteAgent = async (userId) => {
    if (!window.confirm('¿Estás seguro de eliminar este agente?')) return;
    
    try {
      await axios.delete(`${API_URL}/api/users/${userId}`, { withCredentials: true });
      toast.success('Agente eliminado');
      fetchAgents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  const openEditModal = (agent) => {
    setSelectedAgent(agent);
    setFormData({
      name: agent.name,
      email: agent.email,
      phone: agent.phone || '',
      is_active: agent.is_active,
      assigned_careers: agent.assigned_careers || []
    });
    setShowEditModal(true);
  };

  const openResetPasswordModal = (agent) => {
    setSelectedAgent(agent);
    setNewPassword('');
    setShowResetPasswordModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      password: '',
      phone: '',
      assigned_careers: []
    });
  };

  const toggleCareer = (career) => {
    setFormData(prev => ({
      ...prev,
      assigned_careers: prev.assigned_careers.includes(career)
        ? prev.assigned_careers.filter(c => c !== career)
        : [...prev.assigned_careers, career]
    }));
  };

  const getInitials = (name) => {
    if (!name) return 'A';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse" data-testid="agents-loading">
        <div className="h-12 bg-slate-200 rounded-md w-1/3" />
        <div className="h-96 bg-slate-200 rounded-md" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="agents-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Agentes de Ventas
          </h1>
          <p className="text-slate-500 mt-1">
            {agents.length} agente{agents.length !== 1 ? 's' : ''} registrado{agents.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button
          onClick={() => { resetForm(); setShowCreateModal(true); }}
          className="bg-slate-900 hover:bg-slate-800 text-white"
          data-testid="create-agent-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Agente
        </Button>
      </div>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <GraduationCap className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-blue-900">Asignación Automática de Leads</h3>
              <p className="text-sm text-blue-700 mt-1">
                Los leads se asignan automáticamente a los agentes según la carrera de interés del lead 
                y las carreras asignadas a cada agente. Asegúrate de configurar las carreras de cada agente.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agents Table */}
      <Card>
        <CardContent className="p-0">
          {agents.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead className="font-medium">Agente</TableHead>
                    <TableHead className="font-medium">Contacto</TableHead>
                    <TableHead className="font-medium">Carreras Asignadas</TableHead>
                    <TableHead className="font-medium">Estado</TableHead>
                    <TableHead className="font-medium">Registrado</TableHead>
                    <TableHead className="text-right font-medium">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {agents.map((agent) => (
                    <TableRow key={agent.user_id} className="table-row-hover" data-testid={`agent-row-${agent.user_id}`}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-9 w-9">
                            <AvatarImage src={agent.picture} alt={agent.name} />
                            <AvatarFallback className="bg-blue-100 text-blue-600 text-sm">
                              {getInitials(agent.name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium text-slate-900">{agent.name}</p>
                            <p className="text-xs text-slate-500">{agent.user_id}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <span className="text-sm text-slate-600 flex items-center gap-1">
                            <Mail className="w-3 h-3" />
                            {agent.email}
                          </span>
                          {agent.phone && (
                            <span className="text-sm text-slate-600 flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              {agent.phone}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {agent.assigned_careers?.length > 0 ? (
                          <div className="flex flex-wrap gap-1 max-w-[250px]">
                            {agent.assigned_careers.map(career => (
                              <span key={career} className="pill-badge bg-blue-100 text-blue-700 border-blue-200 border text-xs">
                                {career}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded">
                            ⚠️ Sin carreras asignadas
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={`pill-badge ${agent.is_active ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-700 border-slate-200'} border`}>
                          {agent.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm">
                        {new Date(agent.created_at).toLocaleDateString('es-ES')}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" data-testid={`agent-actions-${agent.user_id}`}>
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditModal(agent)}>
                              <Pencil className="w-4 h-4 mr-2" />
                              Editar
                            </DropdownMenuItem>
                            {currentUser?.role === 'admin' && (
                              <DropdownMenuItem onClick={() => openResetPasswordModal(agent)}>
                                <Key className="w-4 h-4 mr-2" />
                                Resetear Contraseña
                              </DropdownMenuItem>
                            )}
                            {currentUser?.role === 'admin' && (
                              <DropdownMenuItem
                                onClick={() => handleDeleteAgent(agent.user_id)}
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
              <Users className="empty-state-icon" />
              <h3 className="text-lg font-medium text-slate-900 mb-1">No hay agentes</h3>
              <p className="text-slate-500 mb-4">Comienza creando el primer agente de ventas</p>
              <Button onClick={() => { resetForm(); setShowCreateModal(true); }}>
                <Plus className="w-4 h-4 mr-2" />
                Nuevo Agente
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Agent Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-md" data-testid="create-agent-modal">
          <DialogHeader>
            <DialogTitle>Nuevo Agente de Ventas</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateAgent} className="space-y-4">
            <div className="form-group">
              <Label htmlFor="name">Nombre completo *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
                data-testid="input-agent-name"
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
                data-testid="input-agent-email"
              />
            </div>
            <div className="form-group">
              <Label htmlFor="password">Contraseña *</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                required
                minLength={6}
                data-testid="input-agent-password"
              />
            </div>
            <div className="form-group">
              <Label htmlFor="phone">Teléfono</Label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                data-testid="input-agent-phone"
              />
            </div>
            <div className="form-group">
              <Label className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4" />
                Carreras Asignadas *
              </Label>
              <p className="text-xs text-slate-500 mb-2">
                Selecciona las carreras que manejará este agente
              </p>
              <div className="grid grid-cols-2 gap-2 p-3 bg-slate-50 rounded-md border max-h-48 overflow-y-auto">
                {CAREERS.map(career => (
                  <label key={career} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-slate-100 p-1 rounded">
                    <Checkbox
                      checked={formData.assigned_careers.includes(career)}
                      onCheckedChange={() => toggleCareer(career)}
                      data-testid={`career-checkbox-${career}`}
                    />
                    <span>{career}</span>
                  </label>
                ))}
              </div>
              {formData.assigned_careers.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {formData.assigned_careers.map(career => (
                    <span key={career} className="pill-badge bg-blue-100 text-blue-700 border-blue-200 border text-xs">
                      {career}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="submit-create-agent">
                Crear Agente
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Agent Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="sm:max-w-md" data-testid="edit-agent-modal">
          <DialogHeader>
            <DialogTitle>Editar Agente</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateAgent} className="space-y-4">
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
              <Label htmlFor="edit-phone">Teléfono</Label>
              <Input
                id="edit-phone"
                value={formData.phone}
                onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <Label>Estado</Label>
              <Select
                value={formData.is_active ? 'active' : 'inactive'}
                onValueChange={(value) => setFormData(prev => ({ ...prev, is_active: value === 'active' }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Activo</SelectItem>
                  <SelectItem value="inactive">Inactivo</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="form-group">
              <Label className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4" />
                Carreras Asignadas
              </Label>
              <p className="text-xs text-slate-500 mb-2">
                Selecciona las carreras que manejará este agente
              </p>
              <div className="grid grid-cols-2 gap-2 p-3 bg-slate-50 rounded-md border max-h-48 overflow-y-auto">
                {CAREERS.map(career => (
                  <label key={career} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-slate-100 p-1 rounded">
                    <Checkbox
                      checked={formData.assigned_careers.includes(career)}
                      onCheckedChange={() => toggleCareer(career)}
                      data-testid={`edit-career-checkbox-${career}`}
                    />
                    <span>{career}</span>
                  </label>
                ))}
              </div>
              {formData.assigned_careers.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {formData.assigned_careers.map(career => (
                    <span key={career} className="pill-badge bg-blue-100 text-blue-700 border-blue-200 border text-xs">
                      {career}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowEditModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="submit-edit-agent">
                Guardar Cambios
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Reset Password Modal */}
      <Dialog open={showResetPasswordModal} onOpenChange={setShowResetPasswordModal}>
        <DialogContent className="sm:max-w-md" data-testid="reset-password-modal">
          <DialogHeader>
            <DialogTitle>Resetear Contraseña</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div className="p-3 bg-slate-50 rounded-md">
              <p className="text-sm text-slate-600">
                Agente: <span className="font-medium">{selectedAgent?.name}</span>
              </p>
              <p className="text-xs text-slate-500">{selectedAgent?.email}</p>
            </div>
            <div className="form-group">
              <Label htmlFor="new-password">Nueva Contraseña *</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
                placeholder="Mínimo 6 caracteres"
                data-testid="input-new-password"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowResetPasswordModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="submit-reset-password">
                Resetear Contraseña
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
