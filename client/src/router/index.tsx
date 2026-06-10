import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import DashboardPage from '@/pages/DashboardPage'
import ProfessorDashboardPage from '@/pages/professor/DashboardPage'
import PortalPage from '@/pages/student/PortalPage'
import DelegatePage from '@/pages/delegado/DelegatePage'
import ContextsPage from '@/pages/professor/ContextsPage'
import GradesPage from '@/pages/professor/GradesPage'
import PublishPage from '@/pages/professor/PublishPage'
import ProfessorCalendarPage from '@/pages/professor/CalendarPage'
import StudentCalendarPage from '@/pages/student/CalendarPage'

function PrivateRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function DelegateRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, role } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (role !== null && role !== 'delegado') {
    if (role === 'professor') return <Navigate to="/painel" replace />
    if (role === 'estudante') return <Navigate to="/portal" replace />
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

function StudentRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, role } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (role !== null && role !== 'estudante') {
    if (role === 'professor') return <Navigate to="/painel" replace />
    if (role === 'delegado') return <Navigate to="/delegado" replace />
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <DashboardPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/painel"
          element={
            <PrivateRoute>
              <ProfessorDashboardPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/portal"
          element={
            <StudentRoute>
              <PortalPage />
            </StudentRoute>
          }
        />
        <Route
          path="/contextos"
          element={
            <PrivateRoute>
              <ContextsPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/notas"
          element={
            <PrivateRoute>
              <GradesPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/delegado"
          element={
            <DelegateRoute>
              <DelegatePage />
            </DelegateRoute>
          }
        />
        <Route
          path="/publicar"
          element={
            <PrivateRoute>
              <PublishPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/calendario"
          element={
            <PrivateRoute>
              <ProfessorCalendarPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/estudante/calendario"
          element={
            <StudentRoute>
              <StudentCalendarPage />
            </StudentRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
