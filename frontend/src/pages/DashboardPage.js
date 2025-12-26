import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
  Users,
  UserPlus,
  Calendar,
  TrendingUp,
  ArrowUpRight,
  ArrowRight,
  Facebook,
  Instagram,
  Music2,
  PenLine
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#64748b'];

const SOURCE_ICONS = {
  facebook: Facebook,
  instagram: Instagram,
  tiktok: Music2,
  manual: PenLine
};

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentLeads, setRecentLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, leadsRes] = await Promise.all([
        axios.get(`${API_URL}/api/dashboard/stats`, { withCredentials: true }),
        axios.get(`${API_URL}/api/dashboard/recent-leads?limit=5`, { withCredentials: true })
      ]);
      setStats(statsRes.data);
      setRecentLeads(leadsRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      nuevo: 'Nuevo',
      contactado: 'Contactado',
      en_progreso: 'En Progreso',
      cita_agendada: 'Cita Agendada',
      convertido: 'Convertido',
      no_interesado: 'No Interesado'
    };
    return labels[status] || status;
  };

  const getSourceIcon = (source) => {
    const Icon = SOURCE_ICONS[source] || Users;
    return Icon;
  };

  const formatChartData = (data) => {
    return Object.entries(data || {}).map(([key, value]) => ({
      name: getStatusLabel(key),
      value: value
    }));
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" data-testid="dashboard-loading">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-md" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 bg-slate-200 rounded-md" />
          <div className="h-80 bg-slate-200 rounded-md" />
        </div>
      </div>
    );
  }

  const statusChartData = formatChartData(stats?.leads_by_status);
  const sourceChartData = formatChartData(stats?.leads_by_source);

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Welcome header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            ¡Hola, {user?.name?.split(' ')[0]}!
          </h1>
          <p className="text-slate-500 mt-1">
            Aquí tienes el resumen de tus leads
          </p>
        </div>
        <Button
          onClick={() => navigate('/leads')}
          className="bg-slate-900 hover:bg-slate-800 text-white"
          data-testid="view-all-leads-btn"
        >
          Ver todos los leads
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <Card className="kpi-card animate-fade-in stagger-1" data-testid="kpi-total-leads">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Leads</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">
                  {stats?.total_leads || 0}
                </p>
              </div>
              <div className="kpi-icon kpi-icon-blue">
                <Users className="w-5 h-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="kpi-card animate-fade-in stagger-2" data-testid="kpi-new-today">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Nuevos Hoy</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">
                  {stats?.new_leads_today || 0}
                </p>
              </div>
              <div className="kpi-icon kpi-icon-green">
                <UserPlus className="w-5 h-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="kpi-card animate-fade-in stagger-3" data-testid="kpi-appointments">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Citas Hoy</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">
                  {stats?.appointments_today || 0}
                </p>
              </div>
              <div className="kpi-icon kpi-icon-amber">
                <Calendar className="w-5 h-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="kpi-card animate-fade-in stagger-4" data-testid="kpi-conversion">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Tasa Conversión</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">
                  {stats?.conversion_rate || 0}%
                </p>
              </div>
              <div className="kpi-icon kpi-icon-purple">
                <TrendingUp className="w-5 h-5" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Chart */}
        <Card className="chart-container" data-testid="status-chart">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-slate-900">
              Leads por Estado
            </CardTitle>
          </CardHeader>
          <CardContent>
            {statusChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={statusChartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" tick={{ fontSize: 12 }} stroke="#64748b" />
                  <YAxis 
                    type="category" 
                    dataKey="name" 
                    width={100} 
                    tick={{ fontSize: 12 }} 
                    stroke="#64748b"
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff', 
                      border: '1px solid #e2e8f0',
                      borderRadius: '6px'
                    }}
                  />
                  <Bar dataKey="value" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-slate-400">
                No hay datos disponibles
              </div>
            )}
          </CardContent>
        </Card>

        {/* Source Chart */}
        <Card className="chart-container" data-testid="source-chart">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-slate-900">
              Leads por Fuente
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sourceChartData.length > 0 ? (
              <div className="flex items-center">
                <ResponsiveContainer width="60%" height={250}>
                  <PieChart>
                    <Pie
                      data={sourceChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {sourceChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="w-40 space-y-2">
                  {sourceChartData.map((entry, index) => (
                    <div key={entry.name} className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <span className="text-sm text-slate-600 capitalize">{entry.name}</span>
                      <span className="text-sm font-medium text-slate-900 ml-auto">{entry.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-slate-400">
                No hay datos disponibles
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Leads */}
      <Card data-testid="recent-leads-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg font-semibold text-slate-900">
            Leads Recientes
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/leads')}
            className="text-slate-500 hover:text-slate-900"
          >
            Ver todos
            <ArrowUpRight className="w-4 h-4 ml-1" />
          </Button>
        </CardHeader>
        <CardContent>
          {recentLeads.length > 0 ? (
            <div className="space-y-3">
              {recentLeads.map((lead) => {
                const SourceIcon = getSourceIcon(lead.source);
                return (
                  <div
                    key={lead.lead_id}
                    className="flex items-center justify-between p-3 rounded-md border border-slate-100 hover:border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/leads/${lead.lead_id}`)}
                    data-testid={`recent-lead-${lead.lead_id}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center source-${lead.source}`}>
                        <SourceIcon className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{lead.full_name}</p>
                        <p className="text-sm text-slate-500">{lead.career_interest}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`pill-badge status-${lead.status} border`}>
                        {getStatusLabel(lead.status)}
                      </span>
                      <p className="text-xs text-slate-400 mt-1">
                        {new Date(lead.created_at).toLocaleDateString('es-ES')}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-400">
              No hay leads recientes
            </div>
          )}
        </CardContent>
      </Card>

      {/* Leads by Agent (only for admin/gerente/supervisor) */}
      {user?.role !== 'agente' && stats?.leads_by_agent && Object.keys(stats.leads_by_agent).length > 0 && (
        <Card data-testid="leads-by-agent-card">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-slate-900">
              Leads por Agente
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.leads_by_agent).map(([agent, count]) => (
                <div key={agent} className="flex items-center justify-between">
                  <span className="text-slate-700">{agent}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${(count / stats.total_leads) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-slate-900 w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
