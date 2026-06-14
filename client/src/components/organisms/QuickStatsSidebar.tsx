import { useEffect, useRef, useState } from 'react'
import { Users, FileText, CheckCircle, XCircle, PhoneOff, Send, AlertTriangle, RefreshCw } from 'lucide-react'
import { StatCard } from '@/components/molecules/StatCard'
import { Button } from '@/components/ui/button'
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
  onReconnect?: () => void
  reconnecting?: boolean
}

const STAT_CARDS: { icon: React.ReactNode; label: string; key: keyof QuickStats; variant?: 'default' | 'success' | 'warning' | 'danger' }[] = [
  { icon: <Users className="size-4" />, label: 'Estudantes', key: 'estudantes' },
  { icon: <FileText className="size-4" />, label: 'Notas', key: 'notas' },
  { icon: <CheckCircle className="size-4" />, label: 'Matched', key: 'matched', variant: 'success' },
  { icon: <XCircle className="size-4" />, label: 'Sem match', key: 'semMatch', variant: 'danger' },
  { icon: <PhoneOff className="size-4" />, label: 'Tel. inválido', key: 'telInvalido', variant: 'warning' },
  { icon: <Send className="size-4" />, label: 'Enviados', key: 'enviados', variant: 'success' },
  { icon: <AlertTriangle className="size-4" />, label: 'Falhas', key: 'falhas', variant: 'danger' },
]

export function QuickStatsSidebar({ stats, onReconnect, reconnecting }: QuickStatsSidebarProps) {
  const [waStatus, setWaStatus] = useState<WhatsAppStatus>({
    connected: false,
    instanceName: 'whatsapp-instance',
  })
  const [checking, setChecking] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const checkWaStatus = async () => {
    setChecking(true)
    try {
      // Use per-professor endpoint; fall back to global status if unauthenticated
      const data = await apiFetch<{ connected: boolean; instance_name: string }>(
        '/api/v1/whatsapp/setup/status',
      ).catch(() =>
        apiFetch<{ connected: boolean; instance_name: string }>('/api/v1/whatsapp/status'),
      )
      setWaStatus({ connected: data.connected, instanceName: data.instance_name })
    } catch {
      // keep current status
    } finally {
      setChecking(false)
    }
  }

  useEffect(() => {
    const initTimer = setTimeout(() => { void checkWaStatus() }, 0)
    pollingRef.current = setInterval(() => { void checkWaStatus() }, 15_000)
    return () => {
      clearTimeout(initTimer)
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  return (
    <aside className="flex flex-col gap-4" aria-label="Estatísticas rápidas">
      <div className="bg-card rounded-lg border border-border p-4">
        <h2 className="text-sm font-semibold text-foreground mb-3 uppercase tracking-wide">
          Estatísticas
        </h2>
        <div className="grid grid-cols-2 gap-2">
          {STAT_CARDS.map(({ icon, label, key, variant }) => (
            <StatCard key={key} icon={icon} label={label} value={stats[key]} variant={variant} />
          ))}
        </div>
      </div>

      {/* WhatsApp Status */}
      <div className="bg-card rounded-lg border border-border p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-foreground uppercase tracking-wide">
            WhatsApp
          </h2>
          <Button
            variant="ghost"
            size="xs"
            onClick={checkWaStatus}
            disabled={checking}
            aria-label="Verificar estado do WhatsApp"
            className="gap-1"
          >
            <RefreshCw className={`size-3 ${checking ? 'animate-spin' : ''}`} />
            {checking ? 'A verificar…' : 'Verificar'}
          </Button>
        </div>

        <div className="flex items-center gap-2 mb-2">
          {waStatus.connected ? (
            <span className="flex items-center gap-1.5 text-sm font-medium text-success">
              <span className="w-2 h-2 rounded-full bg-success inline-block" aria-hidden="true" />
              Conectado ●
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-sm font-medium text-destructive">
              <span className="w-2 h-2 rounded-full bg-destructive inline-block" aria-hidden="true" />
              Desconectado ●
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          Instância: <span className="font-medium text-foreground">{waStatus.instanceName}</span>
        </p>
        <p className="text-xs text-muted-foreground/60 mt-1">Polling automático a cada 15s</p>
        {onReconnect && (
          <Button
            variant="outline"
            size="sm"
            onClick={onReconnect}
            disabled={reconnecting || checking}
            className="text-xs h-7 gap-1.5 mt-2 w-full"
          >
            <RefreshCw className={`size-3 ${reconnecting ? 'animate-spin' : ''}`} />
            {reconnecting ? 'A reconectar…' : 'Reconectar'}
          </Button>
        )}
      </div>
    </aside>
  )
}
