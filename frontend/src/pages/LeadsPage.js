import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
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
  Search,
  Filter,
  MoreVertical,
  Eye,
  Trash2,
  Phone,
  Mail,
  Facebook,
  Instagram,
  Music2,
  PenLine,
  Webhook,
  X,
  Users
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SOURCE_ICONS = {
  facebook: Facebook,
  instagram: Instagram,
  tiktok: Music2,
  manual: PenLine,
  webhook: Webhook
};

const CAREERS = [
  'Ingeniería', 'Medicina', 'Derecho', 'Administración', 
  'Contabilidad', 'Psicología', 'Diseño', 'Marketing', 'Otra'
];

const SOURCES = ['facebook', 'instagram', 'tiktok', 'manual'];

const STATUSES = [
  { value: 'etapa_1_informacion', label: 'Etapa 1 - Información', color: 'bg-blue-100 text-blue-700' },
  { value: 'etapa_2_contacto', label: 'Etapa 2 - Contacto', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'etapa_3_documentacion', label: 'Etapa 3 - Documentación', color: 'bg-purple-100 text-purple-700' },
  { value: 'etapa_4_inscrito', label: 'Etapa 4 - Inscrito', color: 'bg-green-100 text-green-700' },
];

export default function LeadsPage() {
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    source: '',
    career: '',
    agent_id: ''
  });
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    career_interest: '',
    source: 'manual',
    source_detail: '',
    assigned_agent_id: ''
  });

  useEffect(() => {
    fetchLeads();
    if (hasRole(['admin', 'gerente', 'supervisor'])) {
      fetchAgents();
    }
  }, [filters]);

  const fetchLeads = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.source) params.append('source', filters.source);
      if (filters.career) params.append('career', filters.career);
      if (filters.agent_id) params.append('agent_id', filters.agent_id);
      if (searchTerm) params.append('search', searchTerm);

      const response = await axios.get(`${API_URL}/api/leads?${params}`, { withCredentials: true });
      setLeads(response.data);
    } catch (error) {
      console.error('Error fetching leads:', error);
      toast.error('Error al cargar los leads');
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

  const handleSearch = (e) => {
    e.preventDefault();
    fetchLeads();
  };

  const handleCreateLead = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/leads`, formData, { withCredentials: true });
      toast.success('Lead creado exitosamente');
      setShowCreateModal(false);
      setFormData({
        full_name: '',
        email: '',
        phone: '',
        career_interest: '',
        source: 'manual',
        source_detail: '',
        assigned_agent_id: ''
      });
      fetchLeads();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear el lead');
    }
  };

  const handleDeleteLead = async (leadId) => {
    if (!window.confirm('¿Estás seguro de eliminar este lead?')) return;
    
    try {
      await axios.delete(`${API_URL}/api/leads/${leadId}`, { withCredentials: true });
      toast.success('Lead eliminado');
      fetchLeads();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar el lead');
    }
  };

  const clearFilters = () => {
    setFilters({ status: '', source: '', career: '', agent_id: '' });
    setSearchTerm('');
  };

  const getStatusLabel = (status) => {
    const item = STATUSES.find(s => s.value === status);
    return item?.label || status;
  };

  const getSourceIcon = (source) => {
    const Icon = SOURCE_ICONS[source] || PenLine;
    return Icon;
  };

  const activeFiltersCount = Object.values(filters).filter(v => v).length;

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse" data-testid="leads-loading">
        <div className="h-12 bg-slate-200 rounded-md w-1/3" />
        <div className="h-96 bg-slate-200 rounded-md" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="leads-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Leads
          </h1>
          <p className="text-slate-500 mt-1">
            {leads.length} lead{leads.length !== 1 ? 's' : ''} encontrado{leads.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="bg-slate-900 hover:bg-slate-800 text-white"
          data-testid="create-lead-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Lead
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <form onSubmit={handleSearch} className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Buscar por nombre, email o teléfono..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
                data-testid="search-input"
              />
            </form>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className={activeFiltersCount > 0 ? 'border-blue-500 text-blue-600' : ''}
              data-testid="filter-btn"
            >
              <Filter className="w-4 h-4 mr-2" />
              Filtros
              {activeFiltersCount > 0 && (
                <span className="ml-2 w-5 h-5 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center">
                  {activeFiltersCount}
                </span>
              )}
            </Button>
          </div>

          {/* Filter options */}
          {showFilters && (
            <div className="mt-4 p-4 bg-slate-50 rounded-md animate-fade-in" data-testid="filter-panel">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <Label className="text-slate-600 mb-1.5 block text-sm">Estado</Label>
                  <Select
                    value={filters.status || "all"}
                    onValueChange={(value) => setFilters(prev => ({ ...prev, status: value === "all" ? "" : value }))}
                  >
                    <SelectTrigger data-testid="filter-status">
                      <SelectValue placeholder="Todos" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos</SelectItem>
                      {STATUSES.map(s => (
                        <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-slate-600 mb-1.5 block text-sm">Fuente</Label>
                  <Select
                    value={filters.source || "all"}
                    onValueChange={(value) => setFilters(prev => ({ ...prev, source: value === "all" ? "" : value }))}
                  >
                    <SelectTrigger data-testid="filter-source">
                      <SelectValue placeholder="Todas" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas</SelectItem>
                      {SOURCES.map(s => (
                        <SelectItem key={s} value={s} className="capitalize">{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-slate-600 mb-1.5 block text-sm">Carrera</Label>
                  <Select
                    value={filters.career || "all"}
                    onValueChange={(value) => setFilters(prev => ({ ...prev, career: value === "all" ? "" : value }))}
                  >
                    <SelectTrigger data-testid="filter-career">
                      <SelectValue placeholder="Todas" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas</SelectItem>
                      {CAREERS.map(c => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {hasRole(['admin', 'gerente', 'supervisor']) && (
                  <div>
                    <Label className="text-slate-600 mb-1.5 block text-sm">Agente</Label>
                    <Select
                      value={filters.agent_id || "all"}
                      onValueChange={(value) => setFilters(prev => ({ ...prev, agent_id: value === "all" ? "" : value }))}
                    >
                      <SelectTrigger data-testid="filter-agent">
                        <SelectValue placeholder="Todos" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos</SelectItem>
                        {agents.map(a => (
                          <SelectItem key={a.user_id} value={a.user_id}>{a.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>
              <div className="mt-4 flex justify-end">
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  <X className="w-4 h-4 mr-1" />
                  Limpiar filtros
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Leads Table */}
      <Card>
        <CardContent className="p-0">
          {leads.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead className="font-medium">Nombre</TableHead>
                    <TableHead className="font-medium">Contacto</TableHead>
                    <TableHead className="font-medium">Carrera</TableHead>
                    <TableHead className="font-medium">Fuente</TableHead>
                    <TableHead className="font-medium">Estado</TableHead>
                    {hasRole(['admin', 'gerente', 'supervisor']) && (
                      <TableHead className="font-medium">Agente</TableHead>
                    )}
                    <TableHead className="font-medium">Fecha</TableHead>
                    <TableHead className="text-right font-medium">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leads.map((lead) => {
                    const SourceIcon = getSourceIcon(lead.source);
                    return (
                      <TableRow
                        key={lead.lead_id}
                        className="table-row-hover cursor-pointer"
                        onClick={() => navigate(`/leads/${lead.lead_id}`)}
                        data-testid={`lead-row-${lead.lead_id}`}
                      >
                        <TableCell className="font-medium text-slate-900">
                          {lead.full_name}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <span className="text-sm text-slate-600 flex items-center gap-1">
                              <Mail className="w-3 h-3" />
                              {lead.email}
                            </span>
                            <span className="text-sm text-slate-600 flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              {lead.phone}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-slate-600">
                          {lead.career_interest}
                        </TableCell>
                        <TableCell>
                          <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium source-${lead.source}`}>
                            <SourceIcon className="w-3 h-3" />
                            <span className="capitalize">{lead.source}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className={`pill-badge status-${lead.status} border`}>
                            {getStatusLabel(lead.status)}
                          </span>
                        </TableCell>
                        {hasRole(['admin', 'gerente', 'supervisor']) && (
                          <TableCell className="text-slate-600">
                            {lead.assigned_agent_name || 'Sin asignar'}
                          </TableCell>
                        )}
                        <TableCell className="text-slate-500 text-sm">
                          {new Date(lead.created_at).toLocaleDateString('es-ES')}
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                              <Button variant="ghost" size="icon" data-testid={`lead-actions-${lead.lead_id}`}>
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={(e) => { e.stopPropagation(); navigate(`/leads/${lead.lead_id}`); }}>
                                <Eye className="w-4 h-4 mr-2" />
                                Ver detalles
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={(e) => { 
                                  e.stopPropagation(); 
                                  const phone = lead.phone;
                                  navigator.clipboard.writeText(phone).then(() => {
                                    toast.success(`Número copiado: ${phone}`);
                                  }).catch(() => {
                                    toast.error('Error al copiar el número');
                                  });
                                }}
                              >
                                <Phone className="w-4 h-4 mr-2" />
                                Copiar Teléfono
                              </DropdownMenuItem>
                              {hasRole(['admin', 'gerente']) && (
                                <DropdownMenuItem
                                  onClick={(e) => { e.stopPropagation(); handleDeleteLead(lead.lead_id); }}
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
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="empty-state py-16">
              <Users className="empty-state-icon" />
              <h3 className="text-lg font-medium text-slate-900 mb-1">No hay leads</h3>
              <p className="text-slate-500 mb-4">Comienza creando tu primer lead</p>
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Nuevo Lead
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Lead Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-md" data-testid="create-lead-modal">
          <DialogHeader>
            <DialogTitle>Nuevo Lead</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateLead} className="space-y-4">
            <div className="form-group">
              <Label htmlFor="full_name">Nombre completo *</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                required
                data-testid="input-full-name"
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
                data-testid="input-email"
              />
            </div>
            <div className="form-group">
              <Label htmlFor="phone">Teléfono *</Label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                required
                data-testid="input-phone"
              />
            </div>
            <div className="form-group">
              <Label htmlFor="career_interest">Carrera de interés *</Label>
              <Select
                value={formData.career_interest}
                onValueChange={(value) => setFormData(prev => ({ ...prev, career_interest: value }))}
              >
                <SelectTrigger data-testid="select-career">
                  <SelectValue placeholder="Seleccionar" />
                </SelectTrigger>
                <SelectContent>
                  {CAREERS.map(c => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="form-group">
              <Label htmlFor="source">Fuente *</Label>
              <Select
                value={formData.source}
                onValueChange={(value) => setFormData(prev => ({ ...prev, source: value }))}
              >
                <SelectTrigger data-testid="select-source">
                  <SelectValue placeholder="Seleccionar" />
                </SelectTrigger>
                <SelectContent>
                  {SOURCES.map(s => (
                    <SelectItem key={s} value={s} className="capitalize">{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {hasRole(['admin', 'gerente', 'supervisor']) && agents.length > 0 && (
              <div className="form-group">
                <Label htmlFor="assigned_agent_id">Asignar a agente</Label>
                <Select
                  value={formData.assigned_agent_id}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, assigned_agent_id: value }))}
                >
                  <SelectTrigger data-testid="select-agent">
                    <SelectValue placeholder="Seleccionar agente" />
                  </SelectTrigger>
                  <SelectContent>
                    {agents.map(a => (
                      <SelectItem key={a.user_id} value={a.user_id}>{a.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800" data-testid="submit-create-lead">
                Crear Lead
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
