import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
import { toast } from 'sonner';
import {
  Plus,
  Settings,
  Download,
  FileSpreadsheet,
  FileText,
  Trash2,
  Check,
  X,
  Clock,
  History,
  Eye,
  Edit2,
  Shield
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const FIELD_TYPES = [
  { value: 'text', label: 'Texto' },
  { value: 'number', label: 'Número' },
  { value: 'date', label: 'Fecha' },
  { value: 'select', label: 'Lista de opciones' },
  { value: 'checkbox', label: 'Casilla de verificación' },
];

export default function StudentDataPage() {
  const { user: currentUser } = useAuth();
  const [students, setStudents] = useState([]);
  const [customFields, setCustomFields] = useState([]);
  const [changeRequests, setChangeRequests] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFieldModal, setShowFieldModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [editingFields, setEditingFields] = useState({});
  const [newField, setNewField] = useState({
    field_name: '',
    field_type: 'text',
    options: [],
    required: false,
    visible_to_students: true,
    editable_by_supervisor: true
  });
  const [newOption, setNewOption] = useState('');

  const canEdit = ['admin', 'gerente', 'supervisor'].includes(currentUser?.role);
  const canApprove = ['admin', 'gerente'].includes(currentUser?.role);
  const canManageFields = ['admin', 'gerente'].includes(currentUser?.role);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [studentsRes, fieldsRes] = await Promise.all([
        axios.get(`${API_URL}/api/students`, { withCredentials: true }),
        axios.get(`${API_URL}/api/students/custom-fields`, { withCredentials: true })
      ]);
      setStudents(studentsRes.data);
      setCustomFields(fieldsRes.data.fields || []);
      
      if (canApprove) {
        const [requestsRes, logsRes] = await Promise.all([
          axios.get(`${API_URL}/api/change-requests?status=pending`, { withCredentials: true }),
          axios.get(`${API_URL}/api/audit-logs?limit=50`, { withCredentials: true })
        ]);
        setChangeRequests(requestsRes.data.requests || []);
        setAuditLogs(logsRes.data.logs || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateField = async (e) => {
    e.preventDefault();
    if (!newField.field_name.trim()) {
      toast.error('Ingresa un nombre para el campo');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/students/custom-fields`, newField, { withCredentials: true });
      toast.success('Campo creado');
      setShowFieldModal(false);
      setNewField({
        field_name: '',
        field_type: 'text',
        options: [],
        required: false,
        visible_to_students: true,
        editable_by_supervisor: true
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al crear campo');
    }
  };

  const handleDeleteField = async (fieldId) => {
    if (!window.confirm('¿Eliminar este campo? Se perderán todos los datos asociados.')) return;
    try {
      await axios.delete(`${API_URL}/api/students/custom-fields/${fieldId}`, { withCredentials: true });
      toast.success('Campo eliminado');
      fetchData();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const handleSaveStudentFields = async () => {
    try {
      const response = await axios.put(
        `${API_URL}/api/students/${selectedStudent.student_id}/custom-fields`,
        { fields: editingFields },
        { withCredentials: true }
      );
      
      if (response.data.requires_approval) {
        toast.success('Cambios enviados para aprobación');
      } else {
        toast.success('Cambios guardados');
      }
      
      setShowEditModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al guardar');
    }
  };

  const handleApproveRequest = async (requestId) => {
    try {
      await axios.post(`${API_URL}/api/students/change-requests/${requestId}/approve`, {}, { withCredentials: true });
      toast.success('Cambio aprobado');
      fetchData();
    } catch (error) {
      toast.error('Error al aprobar');
    }
  };

  const handleRejectRequest = async (requestId) => {
    const reason = window.prompt('Razón del rechazo (opcional):');
    try {
      await axios.post(`${API_URL}/api/students/change-requests/${requestId}/reject`, { reason }, { withCredentials: true });
      toast.success('Cambio rechazado');
      fetchData();
    } catch (error) {
      toast.error('Error al rechazar');
    }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`${API_URL}/api/students/export/${format}`, {
        withCredentials: true,
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `estudiantes.${format === 'excel' ? 'xlsx' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`Archivo ${format.toUpperCase()} descargado`);
    } catch (error) {
      toast.error('Error al exportar');
    }
  };

  const openEditModal = (student) => {
    setSelectedStudent(student);
    setEditingFields(student.custom_fields || {});
    setShowEditModal(true);
  };

  const addOption = () => {
    if (newOption.trim() && !newField.options.includes(newOption.trim())) {
      setNewField(prev => ({
        ...prev,
        options: [...prev.options, newOption.trim()]
      }));
      setNewOption('');
    }
  };

  const removeOption = (option) => {
    setNewField(prev => ({
      ...prev,
      options: prev.options.filter(o => o !== option)
    }));
  };

  const renderFieldInput = (field, value, onChange) => {
    switch (field.field_type) {
      case 'text':
        return (
          <Input
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={field.field_name}
          />
        );
      case 'number':
        return (
          <Input
            type="number"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
          />
        );
      case 'date':
        return (
          <Input
            type="date"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
          />
        );
      case 'select':
        return (
          <Select value={value || ''} onValueChange={onChange}>
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar..." />
            </SelectTrigger>
            <SelectContent>
              {(field.options || []).map(opt => (
                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      case 'checkbox':
        return (
          <div className="flex items-center gap-2">
            <Checkbox
              checked={value === true || value === 'true'}
              onCheckedChange={(checked) => onChange(checked)}
            />
            <span className="text-sm">{value ? 'Sí' : 'No'}</span>
          </div>
        );
      default:
        return <Input value={value || ''} onChange={(e) => onChange(e.target.value)} />;
    }
  };

  if (loading) {
    return <div className="animate-pulse"><div className="h-96 bg-slate-200 rounded-md" /></div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Base de Datos de Estudiantes
          </h1>
          <p className="text-slate-500 mt-1">
            {students.length} registros • {customFields.length} campos personalizados
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {canApprove && changeRequests.length > 0 && (
            <span className="pill-badge bg-amber-100 text-amber-700 border-amber-200 border">
              {changeRequests.length} pendientes
            </span>
          )}
          <Button variant="outline" onClick={() => handleExport('excel')}>
            <FileSpreadsheet className="w-4 h-4 mr-2" />
            Excel
          </Button>
          <Button variant="outline" onClick={() => handleExport('pdf')}>
            <FileText className="w-4 h-4 mr-2" />
            PDF
          </Button>
          {canManageFields && (
            <Button onClick={() => setShowFieldModal(true)} className="bg-slate-900 hover:bg-slate-800">
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Campo
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="students" className="w-full">
        <TabsList>
          <TabsTrigger value="students">Estudiantes</TabsTrigger>
          {canManageFields && <TabsTrigger value="fields">Campos</TabsTrigger>}
          {canApprove && (
            <TabsTrigger value="approvals" className="relative">
              Aprobaciones
              {changeRequests.length > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs rounded-full px-1.5">
                  {changeRequests.length}
                </span>
              )}
            </TabsTrigger>
          )}
          {canApprove && <TabsTrigger value="audit">Log de Auditoría</TabsTrigger>}
        </TabsList>

        {/* Students Tab */}
        <TabsContent value="students">
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead className="font-medium">Nombre</TableHead>
                      <TableHead className="font-medium">Email</TableHead>
                      <TableHead className="font-medium">Carrera</TableHead>
                      {customFields.slice(0, 5).map(field => (
                        <TableHead key={field.field_id} className="font-medium">
                          {field.field_name}
                        </TableHead>
                      ))}
                      <TableHead className="text-right font-medium">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {students.map((student) => (
                      <TableRow key={student.student_id}>
                        <TableCell className="font-medium">{student.full_name}</TableCell>
                        <TableCell>{student.email}</TableCell>
                        <TableCell>{student.career_name}</TableCell>
                        {customFields.slice(0, 5).map(field => (
                          <TableCell key={field.field_id}>
                            {student.custom_fields?.[field.field_id] !== undefined
                              ? (field.field_type === 'checkbox' 
                                  ? (student.custom_fields[field.field_id] ? '✓' : '✗')
                                  : String(student.custom_fields[field.field_id]))
                              : '-'}
                          </TableCell>
                        ))}
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button variant="ghost" size="sm" onClick={() => openEditModal(student)}>
                              {canEdit ? <Edit2 className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Fields Tab */}
        {canManageFields && (
          <TabsContent value="fields">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Campos Personalizados
                </CardTitle>
              </CardHeader>
              <CardContent>
                {customFields.length > 0 ? (
                  <div className="space-y-2">
                    {customFields.map((field) => (
                      <div key={field.field_id} className="flex items-center justify-between p-3 bg-slate-50 rounded-md">
                        <div>
                          <p className="font-medium">{field.field_name}</p>
                          <div className="flex gap-2 mt-1">
                            <span className="text-xs text-slate-500">Tipo: {field.field_type}</span>
                            {field.required && <span className="text-xs text-red-500">• Requerido</span>}
                            {!field.visible_to_students && <span className="text-xs text-amber-600">• Oculto a alumnos</span>}
                            {!field.editable_by_supervisor && <span className="text-xs text-purple-600">• Solo Admin</span>}
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteField(field.field_id)} className="text-red-600">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-slate-500 py-8">No hay campos personalizados</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Approvals Tab */}
        {canApprove && (
          <TabsContent value="approvals">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Solicitudes de Cambio Pendientes
                </CardTitle>
              </CardHeader>
              <CardContent>
                {changeRequests.length > 0 ? (
                  <div className="space-y-3">
                    {changeRequests.map((req) => (
                      <div key={req.request_id} className="p-4 border rounded-lg">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium">{req.student_name}</p>
                            <p className="text-sm text-slate-600">Campo: {req.field_name}</p>
                            <div className="flex items-center gap-4 mt-2 text-sm">
                              <span className="text-red-600">Antes: {req.old_value || '(vacío)'}</span>
                              <span>→</span>
                              <span className="text-green-600">Después: {req.new_value}</span>
                            </div>
                            <p className="text-xs text-slate-500 mt-2">
                              Solicitado por: {req.requested_by_name} • {new Date(req.created_at).toLocaleString('es-ES')}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <Button size="sm" onClick={() => handleApproveRequest(req.request_id)} className="bg-green-600 hover:bg-green-700">
                              <Check className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleRejectRequest(req.request_id)} className="text-red-600">
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-slate-500 py-8">No hay solicitudes pendientes</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Audit Log Tab */}
        {canApprove && (
          <TabsContent value="audit">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="w-5 h-5" />
                  Log de Auditoría
                </CardTitle>
              </CardHeader>
              <CardContent>
                {auditLogs.length > 0 ? (
                  <div className="space-y-2 max-h-[500px] overflow-y-auto">
                    {auditLogs.map((log) => (
                      <div key={log.log_id} className="p-3 border rounded-md text-sm">
                        <div className="flex items-start justify-between">
                          <div>
                            <span className={`pill-badge text-xs ${
                              log.action === 'create' ? 'bg-green-100 text-green-700' :
                              log.action === 'update' ? 'bg-blue-100 text-blue-700' :
                              log.action === 'delete' ? 'bg-red-100 text-red-700' :
                              'bg-slate-100 text-slate-700'
                            }`}>
                              {log.action}
                            </span>
                            <span className="ml-2 font-medium">{log.entity_type}</span>
                            {log.field_changed && <span className="text-slate-500"> • {log.field_changed}</span>}
                          </div>
                          <span className="text-xs text-slate-400">
                            {new Date(log.timestamp).toLocaleString('es-ES')}
                          </span>
                        </div>
                        <div className="mt-1 text-slate-600">
                          <p>Por: {log.performed_by_name} ({log.performed_by_role})</p>
                          {log.authorized_by_name && (
                            <p className="text-purple-600">Autorizado por: {log.authorized_by_name}</p>
                          )}
                          {log.old_value && log.new_value && (
                            <p className="text-xs mt-1">
                              <span className="text-red-500">{log.old_value}</span>
                              {' → '}
                              <span className="text-green-500">{log.new_value}</span>
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-slate-500 py-8">No hay registros de auditoría</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {/* Create Field Modal */}
      <Dialog open={showFieldModal} onOpenChange={setShowFieldModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Nuevo Campo Personalizado</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateField} className="space-y-4">
            <div className="form-group">
              <Label>Nombre del Campo *</Label>
              <Input
                value={newField.field_name}
                onChange={(e) => setNewField(prev => ({ ...prev, field_name: e.target.value }))}
                placeholder="Ej: Número de Control"
              />
            </div>
            <div className="form-group">
              <Label>Tipo de Campo *</Label>
              <Select
                value={newField.field_type}
                onValueChange={(value) => setNewField(prev => ({ ...prev, field_type: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FIELD_TYPES.map(type => (
                    <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {newField.field_type === 'select' && (
              <div className="form-group">
                <Label>Opciones</Label>
                <div className="flex gap-2">
                  <Input
                    value={newOption}
                    onChange={(e) => setNewOption(e.target.value)}
                    placeholder="Nueva opción"
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addOption())}
                  />
                  <Button type="button" onClick={addOption} variant="outline">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                {newField.options.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {newField.options.map(opt => (
                      <span key={opt} className="pill-badge bg-slate-100 text-slate-700 text-xs flex items-center gap-1">
                        {opt}
                        <button type="button" onClick={() => removeOption(opt)}><X className="w-3 h-3" /></button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={newField.required}
                  onCheckedChange={(checked) => setNewField(prev => ({ ...prev, required: checked }))}
                />
                Campo requerido
              </label>
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={newField.visible_to_students}
                  onCheckedChange={(checked) => setNewField(prev => ({ ...prev, visible_to_students: checked }))}
                />
                Visible para alumnos
              </label>
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={newField.editable_by_supervisor}
                  onCheckedChange={(checked) => setNewField(prev => ({ ...prev, editable_by_supervisor: checked }))}
                />
                Editable por supervisores
              </label>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowFieldModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800">
                Crear Campo
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Student Fields Modal */}
      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {canEdit ? 'Editar' : 'Ver'} Datos - {selectedStudent?.full_name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* Basic info (read-only) */}
            <div className="p-3 bg-slate-50 rounded-md">
              <p className="text-sm"><strong>Email:</strong> {selectedStudent?.email}</p>
              <p className="text-sm"><strong>Carrera:</strong> {selectedStudent?.career_name}</p>
              <p className="text-sm"><strong>Email Inst.:</strong> {selectedStudent?.institutional_email || '-'}</p>
            </div>
            
            {/* Custom fields */}
            {customFields.length > 0 ? (
              <div className="space-y-3">
                <h4 className="font-medium">Campos Adicionales</h4>
                {customFields.map(field => (
                  <div key={field.field_id} className="form-group">
                    <Label className="flex items-center gap-2">
                      {field.field_name}
                      {field.required && <span className="text-red-500">*</span>}
                      {!field.editable_by_supervisor && currentUser?.role === 'supervisor' && (
                        <span className="text-xs text-purple-600">(solo lectura)</span>
                      )}
                    </Label>
                    {canEdit && (field.editable_by_supervisor || ['admin', 'gerente'].includes(currentUser?.role)) ? (
                      renderFieldInput(
                        field,
                        editingFields[field.field_id],
                        (value) => setEditingFields(prev => ({ ...prev, [field.field_id]: value }))
                      )
                    ) : (
                      <p className="text-sm text-slate-600 p-2 bg-slate-50 rounded">
                        {editingFields[field.field_id] !== undefined 
                          ? (field.field_type === 'checkbox' 
                              ? (editingFields[field.field_id] ? 'Sí' : 'No')
                              : String(editingFields[field.field_id]))
                          : '-'}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-4">No hay campos personalizados configurados</p>
            )}
            
            {currentUser?.role === 'supervisor' && (
              <div className="p-3 bg-amber-50 rounded-md text-sm text-amber-800">
                <Clock className="w-4 h-4 inline mr-1" />
                Los cambios serán enviados para aprobación de un Gerente o Admin.
              </div>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setShowEditModal(false)}>
              {canEdit ? 'Cancelar' : 'Cerrar'}
            </Button>
            {canEdit && customFields.length > 0 && (
              <Button onClick={handleSaveStudentFields} className="bg-slate-900 hover:bg-slate-800">
                {currentUser?.role === 'supervisor' ? 'Solicitar Cambios' : 'Guardar'}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
