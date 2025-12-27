import React, { useState, useEffect } from 'react';
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
import { toast } from 'sonner';
import {
  Plus,
  MoreVertical,
  Pencil,
  Trash2,
  Mail,
  Phone,
  GraduationCap,
  FileText,
  Upload,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  School,
  Folder,
  Download
} from 'lucide-react';
import { Avatar, AvatarFallback } from '../components/ui/avatar';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DOCUMENT_TYPES = [
  'INE / Identificación',
  'Certificado de Bachillerato',
  'Acta de Nacimiento',
  'CURP',
  'Comprobante de Domicilio',
  'Fotografía',
  'Comprobante de Pago',
  'Otro'
];

export default function StudentsPage() {
  const { user: currentUser } = useAuth();
  const [students, setStudents] = useState([]);
  const [careers, setCareers] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAttendanceModal, setShowAttendanceModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentType, setDocumentType] = useState('');
  const [attendanceForm, setAttendanceForm] = useState({
    date: new Date().toISOString().split('T')[0],
    subject: '',
    teacher_id: '',
    teacher_name: '',
    status: 'presente',
    notes: ''
  });

  useEffect(() => {
    fetchStudents();
    fetchCareers();
    fetchTeachers();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/students`, { withCredentials: true });
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
      toast.error('Error al cargar los estudiantes');
    } finally {
      setLoading(false);
    }
  };

  const fetchCareers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/careers/full`, { withCredentials: true });
      setCareers(response.data);
    } catch (error) {
      console.error('Error fetching careers:', error);
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

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!selectedFile || !documentType) {
      toast.error('Selecciona un archivo y tipo de documento');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await axios.post(
        `${API_URL}/api/students/${selectedStudent.student_id}/documents?document_type=${encodeURIComponent(documentType)}`,
        formData,
        { 
          withCredentials: true,
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );
      toast.success('Documento subido exitosamente');
      setShowUploadModal(false);
      setSelectedFile(null);
      setDocumentType('');
      // Refresh student data
      const response = await axios.get(`${API_URL}/api/students/${selectedStudent.student_id}`, { withCredentials: true });
      setSelectedStudent(response.data);
      fetchStudents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al subir el documento');
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('¿Eliminar este documento?')) return;
    try {
      await axios.delete(`${API_URL}/api/students/${selectedStudent.student_id}/documents/${documentId}`, { withCredentials: true });
      toast.success('Documento eliminado');
      const response = await axios.get(`${API_URL}/api/students/${selectedStudent.student_id}`, { withCredentials: true });
      setSelectedStudent(response.data);
      fetchStudents();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const handleDownloadDocument = async (documentId, filename) => {
    try {
      const response = await axios.get(
        `${API_URL}/api/students/${selectedStudent.student_id}/documents/${documentId}/download`,
        { 
          withCredentials: true,
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Documento descargado');
    } catch (error) {
      toast.error('Error al descargar el documento');
    }
  };

  const handleRecordAttendance = async (e) => {
    e.preventDefault();
    if (!attendanceForm.subject) {
      toast.error('Selecciona una materia');
      return;
    }

    try {
      await axios.post(
        `${API_URL}/api/students/${selectedStudent.student_id}/attendance`,
        attendanceForm,
        { withCredentials: true }
      );
      toast.success('Asistencia registrada');
      setShowAttendanceModal(false);
      // Refresh student data
      const response = await axios.get(`${API_URL}/api/students/${selectedStudent.student_id}`, { withCredentials: true });
      setSelectedStudent(response.data);
    } catch (error) {
      toast.error('Error al registrar asistencia');
    }
  };

  const handleDeleteStudent = async (studentId) => {
    if (!window.confirm('¿Eliminar este estudiante y todos sus documentos?')) return;
    try {
      await axios.delete(`${API_URL}/api/students/${studentId}`, { withCredentials: true });
      toast.success('Estudiante eliminado');
      setShowDetailModal(false);
      fetchStudents();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  const openDetailModal = async (student) => {
    try {
      const response = await axios.get(`${API_URL}/api/students/${student.student_id}`, { withCredentials: true });
      setSelectedStudent(response.data);
      setShowDetailModal(true);
    } catch (error) {
      toast.error('Error al cargar detalles');
    }
  };

  const getInitials = (name) => {
    if (!name) return 'E';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getAttendanceIcon = (status) => {
    switch (status) {
      case 'presente': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'ausente': return <XCircle className="w-4 h-4 text-red-600" />;
      case 'justificado': return <Clock className="w-4 h-4 text-yellow-600" />;
      default: return null;
    }
  };

  const getCareerSchedules = () => {
    if (!selectedStudent) return [];
    const career = careers.find(c => c.career_id === selectedStudent.career_id);
    return career?.schedules || [];
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
            Estudiantes
          </h1>
          <p className="text-slate-500 mt-1">
            {students.length} estudiante{students.length !== 1 ? 's' : ''} inscrito{students.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Info Card */}
      <Card className="bg-green-50 border-green-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <School className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-green-900">Gestión de Estudiantes</h3>
              <p className="text-sm text-green-700 mt-1">
                Los estudiantes se crean automáticamente cuando un Lead completa la Etapa 4 (Inscrito). 
                Aquí puedes gestionar sus documentos, horarios asignados y registro de asistencia.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Students Table */}
      <Card>
        <CardContent className="p-0">
          {students.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead className="font-medium">Estudiante</TableHead>
                    <TableHead className="font-medium">Carrera</TableHead>
                    <TableHead className="font-medium">Contacto</TableHead>
                    <TableHead className="font-medium">Email Institucional</TableHead>
                    <TableHead className="font-medium">Documentos</TableHead>
                    <TableHead className="font-medium">Inscrito</TableHead>
                    <TableHead className="text-right font-medium">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {students.map((student) => (
                    <TableRow key={student.student_id} className="table-row-hover cursor-pointer" onClick={() => openDetailModal(student)}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-9 w-9">
                            <AvatarFallback className="bg-green-100 text-green-600 text-sm">
                              {getInitials(student.full_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium text-slate-900">{student.full_name}</p>
                            <p className="text-xs text-slate-500">{student.student_id}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="pill-badge bg-slate-100 text-slate-700 border-slate-200 border text-xs">
                          {student.career_name}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <span className="text-sm text-slate-600 flex items-center gap-1">
                            <Mail className="w-3 h-3" />
                            {student.email}
                          </span>
                          <span className="text-sm text-slate-600 flex items-center gap-1">
                            <Phone className="w-3 h-3" />
                            {student.phone}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {student.institutional_email ? (
                          <span className="text-sm text-blue-600">{student.institutional_email}</span>
                        ) : (
                          <span className="text-xs text-slate-400">No asignado</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Folder className="w-4 h-4 text-slate-400" />
                          <span className="text-sm">{student.documents?.length || 0}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm">
                        {new Date(student.created_at).toLocaleDateString('es-ES')}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); openDetailModal(student); }}>
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="empty-state py-16">
              <School className="empty-state-icon" />
              <h3 className="text-lg font-medium text-slate-900 mb-1">No hay estudiantes</h3>
              <p className="text-slate-500 mb-4">Los estudiantes aparecerán cuando conviertas leads de la Etapa 4</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Student Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-green-100 text-green-600 text-sm">
                  {getInitials(selectedStudent?.full_name)}
                </AvatarFallback>
              </Avatar>
              {selectedStudent?.full_name}
            </DialogTitle>
          </DialogHeader>
          
          {selectedStudent && (
            <Tabs defaultValue="info" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="info">Información</TabsTrigger>
                <TabsTrigger value="documents">Documentos</TabsTrigger>
                <TabsTrigger value="schedule">Horario</TabsTrigger>
                <TabsTrigger value="attendance">Asistencia</TabsTrigger>
              </TabsList>
              
              {/* Info Tab */}
              <TabsContent value="info" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-50 rounded-md">
                    <p className="text-xs text-slate-500">ID Estudiante</p>
                    <p className="font-medium">{selectedStudent.student_id}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-md">
                    <p className="text-xs text-slate-500">Carrera</p>
                    <p className="font-medium">{selectedStudent.career_name}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-md">
                    <p className="text-xs text-slate-500">Email Personal</p>
                    <p className="font-medium">{selectedStudent.email}</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-md">
                    <p className="text-xs text-slate-500">Teléfono</p>
                    <p className="font-medium">{selectedStudent.phone}</p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-md col-span-2">
                    <p className="text-xs text-blue-600">Email Institucional</p>
                    <p className="font-medium text-blue-900">
                      {selectedStudent.institutional_email || 'No asignado - Editar para asignar'}
                    </p>
                  </div>
                </div>
                
                {currentUser?.role === 'admin' && (
                  <div className="flex justify-end">
                    <Button variant="destructive" size="sm" onClick={() => handleDeleteStudent(selectedStudent.student_id)}>
                      <Trash2 className="w-4 h-4 mr-1" />
                      Eliminar Estudiante
                    </Button>
                  </div>
                )}
              </TabsContent>
              
              {/* Documents Tab */}
              <TabsContent value="documents" className="space-y-4">
                <div className="flex justify-between items-center">
                  <p className="text-sm text-slate-600">
                    {selectedStudent.documents?.length || 0} documento(s) subido(s)
                  </p>
                  <Button size="sm" onClick={() => setShowUploadModal(true)}>
                    <Upload className="w-4 h-4 mr-1" />
                    Subir Documento
                  </Button>
                </div>
                
                {selectedStudent.documents?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedStudent.documents.map((doc) => (
                      <div key={doc.document_id} className="flex items-center justify-between p-3 bg-slate-50 rounded-md">
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-slate-400" />
                          <div>
                            <p className="font-medium text-sm">{doc.name}</p>
                            <p className="text-xs text-slate-500">{doc.original_filename || doc.filename}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400">
                            {new Date(doc.uploaded_at).toLocaleDateString('es-ES')}
                          </span>
                          <Button variant="ghost" size="sm" onClick={() => handleDeleteDocument(doc.document_id)} className="text-red-600 h-8 w-8 p-0">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <FileText className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>No hay documentos subidos</p>
                  </div>
                )}
                
                <div className="p-3 bg-amber-50 rounded-md text-sm">
                  <p className="text-amber-800">
                    <strong>📁 Carpeta de documentos:</strong> /app/student_documents/{selectedStudent.student_id}/
                  </p>
                  <p className="text-amber-700 text-xs mt-1">
                    Para acceso VPN, configura tu servidor para exponer este directorio.
                  </p>
                </div>
              </TabsContent>
              
              {/* Schedule Tab */}
              <TabsContent value="schedule" className="space-y-4">
                {getCareerSchedules().length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Materia</TableHead>
                        <TableHead>Maestro</TableHead>
                        <TableHead>Día</TableHead>
                        <TableHead>Horario</TableHead>
                        <TableHead>Modalidad</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {getCareerSchedules().map((schedule, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-medium">{schedule.subject}</TableCell>
                          <TableCell>{schedule.teacher_name || '-'}</TableCell>
                          <TableCell className="capitalize">{schedule.day}</TableCell>
                          <TableCell>{schedule.start_time} - {schedule.end_time}</TableCell>
                          <TableCell>
                            <span className={`pill-badge text-xs ${schedule.mode === 'presencial' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                              {schedule.mode}
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <Calendar className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>No hay horarios configurados para esta carrera</p>
                    <p className="text-xs">Configura los horarios en la sección de Carreras</p>
                  </div>
                )}
              </TabsContent>
              
              {/* Attendance Tab */}
              <TabsContent value="attendance" className="space-y-4">
                <div className="flex justify-between items-center">
                  <p className="text-sm text-slate-600">
                    {selectedStudent.attendance?.length || 0} registro(s) de asistencia
                  </p>
                  <Button size="sm" onClick={() => {
                    setAttendanceForm({
                      date: new Date().toISOString().split('T')[0],
                      subject: '',
                      teacher_id: '',
                      teacher_name: '',
                      status: 'presente',
                      notes: ''
                    });
                    setShowAttendanceModal(true);
                  }}>
                    <Plus className="w-4 h-4 mr-1" />
                    Registrar Asistencia
                  </Button>
                </div>
                
                {selectedStudent.attendance?.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fecha</TableHead>
                        <TableHead>Materia</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Notas</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedStudent.attendance.slice().reverse().map((att, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{new Date(att.date).toLocaleDateString('es-ES')}</TableCell>
                          <TableCell>{att.subject}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              {getAttendanceIcon(att.status)}
                              <span className="capitalize">{att.status}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-sm text-slate-500">{att.notes || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <CheckCircle className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p>No hay registros de asistencia</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>

      {/* Upload Document Modal */}
      <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Subir Documento</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUploadDocument} className="space-y-4">
            <div className="form-group">
              <Label>Tipo de Documento *</Label>
              <Select value={documentType} onValueChange={setDocumentType}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar tipo" />
                </SelectTrigger>
                <SelectContent>
                  {DOCUMENT_TYPES.map(type => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="form-group">
              <Label>Archivo *</Label>
              <Input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                onChange={(e) => setSelectedFile(e.target.files[0])}
              />
              <p className="text-xs text-slate-500 mt-1">
                Formatos permitidos: PDF, JPG, PNG, DOC, DOCX
              </p>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowUploadModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800">
                Subir
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Record Attendance Modal */}
      <Dialog open={showAttendanceModal} onOpenChange={setShowAttendanceModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Registrar Asistencia</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleRecordAttendance} className="space-y-4">
            <div className="form-group">
              <Label>Fecha *</Label>
              <Input
                type="date"
                value={attendanceForm.date}
                onChange={(e) => setAttendanceForm(prev => ({ ...prev, date: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <Label>Materia *</Label>
              <Select
                value={attendanceForm.subject}
                onValueChange={(value) => {
                  const schedule = getCareerSchedules().find(s => s.subject === value);
                  setAttendanceForm(prev => ({
                    ...prev,
                    subject: value,
                    teacher_id: schedule?.teacher_id || '',
                    teacher_name: schedule?.teacher_name || ''
                  }));
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccionar materia" />
                </SelectTrigger>
                <SelectContent>
                  {getCareerSchedules().map((schedule, idx) => (
                    <SelectItem key={idx} value={schedule.subject}>{schedule.subject}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="form-group">
              <Label>Estado *</Label>
              <Select
                value={attendanceForm.status}
                onValueChange={(value) => setAttendanceForm(prev => ({ ...prev, status: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="presente">✓ Presente</SelectItem>
                  <SelectItem value="ausente">✗ Ausente</SelectItem>
                  <SelectItem value="justificado">⏱ Justificado</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="form-group">
              <Label>Notas (opcional)</Label>
              <Input
                value={attendanceForm.notes}
                onChange={(e) => setAttendanceForm(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Observaciones..."
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowAttendanceModal(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-slate-900 hover:bg-slate-800">
                Registrar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
