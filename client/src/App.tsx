import { AuthProvider } from '@/contexts/AuthContext'
import { ActiveContextProvider } from '@/contexts/ActiveContextContext'
import { AppRouter } from '@/router'

// Componente raiz: envolve toda a app em "Providers" (contextos partilhados) e
// no AppRouter (que decide que página mostrar conforme o endereço).
// - AuthProvider: disponibiliza a quem está autenticado a todas as páginas.
// - ActiveContextProvider: guarda qual a turma/disciplina seleccionada.
export default function App() {
  return (
    <AuthProvider>
      <ActiveContextProvider>
        <AppRouter />
      </ActiveContextProvider>
    </AuthProvider>
  )
}
