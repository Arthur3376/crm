import React, { useRef, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Toaster } from './components/ui/sonner';

// Suppress ResizeObserver error overlay
useEffect(() => {
  const hideOverlay = () => {
    const overlay = document.getElementById('webpack-dev-server-client-overlay');
    if (overlay) overlay.style.display = 'none';
  };
  
  const observer = new MutationObserver(hideOverlay);
  observer.observe(document.body, { childList: true, subtree: true });
  
  return () => observer.disconnect();
}, []);

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import LeadsPage from './pages/LeadsPage';
import LeadDetailPage from './pages/LeadDetailPage';
import UsersPage from './pages/UsersPage';
import CalendarPage from './pages/CalendarPage';
import WebhooksPage from './pages/WebhooksPage';
import NotificationsPage from './pages/NotificationsPage';

// Layout
import DashboardLayout from './layouts/DashboardLayout';

import './App.css';

// Auth Callback Component - Processes Google OAuth session
const AuthCallback = () => {
  const navigate = useNavigate();
  const { processGoogleSession } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Use ref to prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processSession = async () => {
      const hash = window.location.hash;
      const params = new URLSearchParams(hash.substring(1));
      const sessionId = params.get('session_id');

      if (sessionId) {
        try {
          await processGoogleSession(sessionId);
          // Clear hash and navigate to dashboard
          window.history.replaceState(null, '', window.location.pathname);
          navigate('/dashboard', { replace: true });
        } catch (error) {
          console.error('Failed to process session:', error);
          navigate('/login', { replace: true });
        }
      } else {
        navigate('/login', { replace: true });
      }
    };

    processSession();
  }, [navigate, processGoogleSession]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="animate-pulse text-slate-500">Procesando autenticación...</div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-pulse text-slate-500">Cargando...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// App Router - Detects session_id synchronously before routes
const AppRouter = () => {
  const location = useLocation();
  
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  // Check URL fragment for session_id synchronously during render
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected Routes with Dashboard Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="leads" element={<LeadsPage />} />
        <Route path="leads/:leadId" element={<LeadDetailPage />} />
        <Route
          path="users"
          element={
            <ProtectedRoute allowedRoles={['admin', 'gerente']}>
              <UsersPage />
            </ProtectedRoute>
          }
        />
        <Route path="calendar" element={<CalendarPage />} />
        <Route
          path="webhooks"
          element={
            <ProtectedRoute allowedRoles={['admin', 'gerente']}>
              <WebhooksPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="notifications"
          element={
            <ProtectedRoute allowedRoles={['admin', 'gerente']}>
              <NotificationsPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch all - redirect to dashboard */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
