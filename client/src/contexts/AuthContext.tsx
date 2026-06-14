import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { User } from '@/types'

interface LoginCredentials {
  email_or_student_number: string
  password: string
  role: 'professor' | 'estudante' | 'delegado'
}

interface ChangePasswordPayload {
  new_password: string
  confirm_password: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  role: User['role'] | null
  requiresPasswordChange: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  changePassword: (payload: ChangePasswordPayload) => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

function loadUserFromStorage(): User | null {
  try {
    const stored = localStorage.getItem('auth_user')
    if (!stored) return null

    const user = JSON.parse(stored) as User

    // Rejeitar dados mock/demo
    if (user.name?.includes('Demo') || user.name?.includes('Mock') || user.id === 'mock-user-1') {
      localStorage.removeItem('auth_user')
      return null
    }

    // Validar que token existe (não é string vazia ou mock)
    if (!user.token || user.token === 'mock-token-dev' || user.token.length < 10) {
      localStorage.removeItem('auth_user')
      return null
    }

    return user
  } catch {
    localStorage.removeItem('auth_user')
    return null
  }
}

interface LoginApiResponse {
  id: string
  name: string
  role: User['role']
  access_token: string
  requires_password_change?: boolean
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(loadUserFromStorage)
  const [requiresPasswordChange, setRequiresPasswordChange] = useState(false)

  const login = async (credentials: LoginCredentials) => {
    const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
    const res = await fetch(`${base}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    })

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText })) as { detail?: string }
      throw new Error(error.detail ?? `Login failed: ${res.status}`)
    }

    const data = await res.json() as LoginApiResponse
    const userData: User = {
      id: data.id,
      name: data.name,
      role: data.role,
      token: data.access_token,
    }
    setUser(userData)
    localStorage.setItem('auth_user', JSON.stringify(userData))
    setRequiresPasswordChange(data.requires_password_change ?? false)
  }

  const logout = () => {
    setUser(null)
    setRequiresPasswordChange(false)
    localStorage.removeItem('auth_user')
  }

  const changePassword = async (payload: ChangePasswordPayload) => {
    const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
    const stored = localStorage.getItem('auth_user')
    const token: string | null = stored
      ? (JSON.parse(stored) as { token: string }).token
      : null

    const res = await fetch(`${base}/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText })) as { detail?: string }
      throw new Error(err.detail ?? `Change password failed: ${res.status}`)
    }

    setRequiresPasswordChange(false)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        role: user?.role ?? null,
        requiresPasswordChange,
        login,
        logout,
        changePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
