import { useEffect, useRef, useState } from 'react'
import { StatCard } from '@/components/molecules/StatCard'
import { Badge } from '@/components/ui/badge'
import { apiFetch } from '@/lib/api'

interface QuickStats {
  estudantes: number
  notas: number
  matched: number
  semMatch: number
  telInvalido: number
  enviados: number
  falhas: number
}

interface WhatsAppStatus {
  connected: boolean
  instanceName: string
}

interface QuickStatsSidebarProps {
  stats: QuickStats
}

const STAT_CARDS: { icon: string; label: string; key: keyof QuickStats }[] = [
  { icon: '👥', label: 'Estudantes', key: 'estudantes' },
  { icon: '📝', label: 'Notas', key: 'notas' },
  { icon: '✅', label: 'Matched', key: 'matched' },
  { icon: '❌', label: 'Sem match', key: 'semMatch' },
  { icon: '📵', label: 'Tel. inválido', key: 'telInvalido' },
  { icon: '📤', label: 'Enviados', key: 'enviados' },
  { icon: '⚠️', label: 'Falhas', key: 'falhas' },
]

export function QuickStatsSidebar({ stats }: QuickStatsSidebarProps) {
  const [waStatus, setWaStatus] = useState<WhatsAppStatus>({
    connected: false,
    instanceName: 'whatsapp-instance',
  })
  const [checking, setChecking] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const checkWaStatus = async () => {
    setChecking(true)
    try {
      const data = await apiFetch<{ connected: boolean; instance_name: string }>(
        '/whatsapp/status',
      )
      setWaStatus({ connected: data.connected, instanceName: data.instance_name })
    } catch {
      // Mock: keep current status
    } finally {
      setChecking(false)
    }
  }

  useEffect(() => {
    // Schedule polling; initial check runs after mount via the interval's first tick
    // Kick off first check via timeout so it runs asynchronously (not synchronously in effect)
    const initTimer = setTimeout(() => { void checkWaStatus() }, 0)
    pollingRef.current = setInterval(() => { void checkWaStatus() }, 30_000)
    return () => {
      clearTimeout(initTimer)
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  return (
    <aside className="flex flex-col gap-4" aria-label="Estatísticas rápidas">
      {/* Quick Stats */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3 uppercase tracking-wide">
          Estatísticas
        </h2>
        <div className="grid grid-cols-2 gap-2">
          {STAT_CARDS.map(({ icon, label, key }) => (
            <StatCard key={key} icon={icon} label={label} value={stats[key]} />
          ))}
        </div>
      </div>

      {/* WhatsApp Status */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            WhatsApp
          </h2>
          <button
            type="button"
            onClick={checkWaStatus}
            disabled={checking}
            className="text-xs text-[#0D6EFD] hover:underline disabled:opacity-50"
            aria-label="Verificar estado do WhatsApp"
          >
            {checking ? 'A verificar…' : 'Verificar estado'}
          </button>
        </div>

        <div className="flex items-center gap-2 mb-2">
          <Badge
            className={
              waStatus.connected
                ? 'bg-[#15803D] hover:bg-[#15803D] text-white'
                : 'bg-[#B91C1C] hover:bg-[#B91C1C] text-white'
            }
          >
            {waStatus.connected ? '● Conectado' : '● Desconectado'}
          </Badge>
        </div>
        <p className="text-xs text-slate-500">
          Instância: <span className="font-medium text-slate-700">{waStatus.instanceName}</span>
        </p>
        <p className="text-xs text-slate-400 mt-1">Polling automático a cada 30s</p>
      </div>
    </aside>
  )
}
