import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Users,
  UserCircle,
  Calendar,
  Webhook,
  Bell,
  LogOut,
  Menu,
  X,
  ChevronDown,
  GraduationCap
} from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Button } from '../components/ui/button';

const DashboardLayout = () => {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      roles: ['admin', 'gerente', 'supervisor', 'agente']
    },
    {
      path: '/leads',
      label: 'Leads',
      icon: Users,
      roles: ['admin', 'gerente', 'supervisor', 'agente']
    },
    {
      path: '/calendar',
      label: 'Calendario',
      icon: Calendar,
      roles: ['admin', 'gerente', 'supervisor', 'agente']
    },
    {
      path: '/agents',
      label: 'Agentes',
      icon: GraduationCap,
      roles: ['admin', 'gerente']
    },
    {
      path: '/users',
      label: 'Usuarios',
      icon: UserCircle,
      roles: ['admin']
    },
    {
      path: '/webhooks',
      label: 'Webhooks',
      icon: Webhook,
      roles: ['admin', 'gerente']
    },
    {
      path: '/notifications',
      label: 'Notificaciones',
      icon: Bell,
      roles: ['admin', 'gerente']
    }
  ];

  const filteredNavItems = navItems.filter(item => hasRole(item.roles));

  const getRoleBadgeClass = (role) => {
    const classes = {
      admin: 'role-admin',
      gerente: 'role-gerente',
      supervisor: 'role-supervisor',
      agente: 'role-agente'
    };
    return classes[role] || 'role-agente';
  };

  const getRoleLabel = (role) => {
    const labels = {
      admin: 'Administrador',
      gerente: 'Gerente',
      supervisor: 'Supervisor',
      agente: 'Agente'
    };
    return labels[role] || role;
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="dashboard-layout">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-slate-200 transform transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        data-testid="sidebar"
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-slate-900 rounded-md flex items-center justify-center">
              <span className="text-white font-bold text-sm">UC</span>
            </div>
            <span className="font-semibold text-slate-900 text-lg tracking-tight">UCIC</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 hover:bg-slate-100 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1" data-testid="sidebar-nav">
          {filteredNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
              data-testid={`nav-${item.path.replace('/', '')}`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User info at bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-200">
          <div className="flex items-center gap-3">
            <Avatar className="h-9 w-9">
              <AvatarImage src={user?.picture} alt={user?.name} />
              <AvatarFallback className="bg-slate-200 text-slate-600 text-sm">
                {getInitials(user?.name)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
              <span className={`pill-badge ${getRoleBadgeClass(user?.role)} border`}>
                {getRoleLabel(user?.role)}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Header */}
        <header className="sticky top-0 z-30 h-16 glass-header border-b border-slate-200/50" data-testid="header">
          <div className="h-full px-4 md:px-6 flex items-center justify-between">
            {/* Mobile menu button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 hover:bg-slate-100 rounded-md"
              data-testid="mobile-menu-btn"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Page title area - can be customized per page */}
            <div className="hidden lg:block" />

            {/* Right side actions */}
            <div className="flex items-center gap-3">
              {/* Notifications */}
              <Button variant="ghost" size="icon" className="relative" data-testid="notifications-btn">
                <Bell className="w-5 h-5 text-slate-500" />
                <span className="notification-dot" />
              </Button>

              {/* User menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2 px-2" data-testid="user-menu-btn">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={user?.picture} alt={user?.name} />
                      <AvatarFallback className="bg-slate-200 text-slate-600 text-xs">
                        {getInitials(user?.name)}
                      </AvatarFallback>
                    </Avatar>
                    <span className="hidden md:block text-sm font-medium text-slate-700">
                      {user?.name?.split(' ')[0]}
                    </span>
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-2 py-1.5">
                    <p className="text-sm font-medium text-slate-900">{user?.name}</p>
                    <p className="text-xs text-slate-500">{user?.email}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600 cursor-pointer" data-testid="logout-btn">
                    <LogOut className="w-4 h-4 mr-2" />
                    Cerrar sesión
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6 lg:p-8" data-testid="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
