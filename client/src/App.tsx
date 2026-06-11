import { AuthProvider } from '@/contexts/AuthContext'
import { ActiveContextProvider } from '@/contexts/ActiveContextContext'
import { AppRouter } from '@/router'

export default function App() {
  return (
    <AuthProvider>
      <ActiveContextProvider>
        <AppRouter />
      </ActiveContextProvider>
    </AuthProvider>
  )
}
