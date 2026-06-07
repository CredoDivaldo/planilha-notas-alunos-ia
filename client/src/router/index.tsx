import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ProfessorDashboardPage from '@/pages/professor/DashboardPage'
import PortalPage from '@/pages/student/PortalPage'
import DelegatePage from '@/pages/delegado/DelegatePage'
import ContextsPage from '@/pages/professor/ContextsPage'
import GradesPage from '@/pages/professor/GradesPage'

function PrivateRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
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
            <PrivateRoute>
              <PortalPage />
            </PrivateRoute>
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
            <PrivateRoute>
              <DelegatePage />
            </PrivateRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
