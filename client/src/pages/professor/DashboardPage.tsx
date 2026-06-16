// Professor panel — profile + WhatsApp status + CSV templates + change password.
// Upload of students lives in Contextos, grades in Notas, and dispatch in Publicar.

import { useEffect, useRef, useState, useCallback } from 'react'
import { Smartphone, Download, KeyRound, RefreshCw, CheckCircle, XCircle, BookOpen, Users, GraduationCap } from 'lucide-react'
import { AppHeader } from '@/components/organisms/AppHeader'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import { apiFetch } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'

interface Profile {
  id: string
  name: string
  role: string
  disciplines: string[]
  contexts_count: number
}

// ---------------------------------------------------------------------------
// CSV template generation (download via Blob) — columns aligned to the parser
// ---------------------------------------------------------------------------

function downloadCsv(filename: string, content: string) {
  // UTF-8 BOM so Excel opens accents correctly
  const blob = new Blob(['﻿' + content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const STUDENTS_TEMPLATE = 'numero_estudante,nome,turma,whatsapp\n2026001,Nome do Estudante,10A,244900000000\n'
const GRADES_TEMPLATE = 'numero_estudante,nome,nota,turma\n2026001,Nome do Estudante,15,10A\n'

export default function DashboardPage() {
  const { changePassword } = useAuth()

  // ─── Profile ──────────────────────────────────────────────────────────────
  const [profile, setProfile] = useState<Profile | null>(null)
  useEffect(() => {
    apiFetch<Profile>('/auth/me')
      .then(setProfile)
      .catch(() => setProfile(null))
  }, [])

  // ─── WhatsApp status + QR ───────────────────────────────────────────────────
  const [waConnected, setWaConnected] = useState(false)
  const [waChecking, setWaChecking] = useState(true)
  const [qrCode, setQrCode] = useState<string | null>(null)
  const [qrLoading, setQrLoading] = useState(false)
  const [qrError, setQrError] = useState<string | null>(null)
  const [qrOpen, setQrOpen] = useState(false)
  const qrPollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const statusPollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const checkStatus = useCallback(async () => {
    setWaChecking(true)
    try {
      const data = await apiFetch<{ connected: boolean }>('/api/v1/whatsapp/setup/status')
      setWaConnected(data.connected)
      return data.connected
    } catch {
      setWaConnected(false)
      return false
    } finally {
      setWaChecking(false)
    }
  }, [])

  const fetchQr = useCallback(async () => {
    setQrLoading(true)
    setQrError(null)
    try {
      await apiFetch('/api/v1/whatsapp/setup/create', { method: 'POST' }).catch(() => {})
      const data = await apiFetch<{ code: string | null; simulated?: boolean }>('/api/v1/whatsapp/setup/qr')
      const isImage = data.code && (data.code.startsWith('data:') || data.code.startsWith('http'))
      if (isImage) {
        setQrCode(data.code)
      } else if (data.simulated) {
        setQrError('Evolution API não configurada (EVOLUTION_API_URL).')
      } else {
        setQrError('QR indisponível. Verifique a Evolution API.')
      }
    } catch {
      setQrError('Erro ao contactar a Evolution API.')
    } finally {
      setQrLoading(false)
    }
  }, [])

  useEffect(() => {
    void checkStatus()
    return () => {
      if (qrPollRef.current) clearInterval(qrPollRef.current)
      if (statusPollRef.current) clearInterval(statusPollRef.current)
    }
  }, [checkStatus])

  const openQr = () => {
    setQrOpen(true)
    void fetchQr()
    if (qrPollRef.current) clearInterval(qrPollRef.current)
    if (statusPollRef.current) clearInterval(statusPollRef.current)
    qrPollRef.current = setInterval(() => { void fetchQr() }, 6000)
    statusPollRef.current = setInterval(async () => {
      const connected = await checkStatus()
      if (connected) {
        setQrOpen(false)
        if (qrPollRef.current) clearInterval(qrPollRef.current)
        if (statusPollRef.current) clearInterval(statusPollRef.current)
      }
    }, 5000)
  }

  const closeQr = () => {
    setQrOpen(false)
    if (qrPollRef.current) clearInterval(qrPollRef.current)
    if (statusPollRef.current) clearInterval(statusPollRef.current)
  }

  // ─── Change password ────────────────────────────────────────────────────────
  const [pwOpen, setPwOpen] = useState(false)
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [pwError, setPwError] = useState<string | null>(null)
  const [pwOk, setPwOk] = useState(false)
  const [pwLoading, setPwLoading] = useState(false)

  const hasMinLen = newPw.length >= 8
  const hasUpper = /[A-Z]/.test(newPw)
  const pwMatch = newPw.length > 0 && newPw === confirmPw
  const canChangePw = hasMinLen && hasUpper && pwMatch && !pwLoading

  const submitPw = async () => {
    setPwLoading(true)
    setPwError(null)
    try {
      await changePassword({ new_password: newPw, confirm_password: confirmPw })
      setPwOk(true)
      setNewPw('')
      setConfirmPw('')
      setTimeout(() => { setPwOpen(false); setPwOk(false) }, 1500)
    } catch (err) {
      setPwError(err instanceof Error ? err.message : 'Erro ao alterar palavra-passe.')
    } finally {
      setPwLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <AppHeader activeTab="painel" />
      <main className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-6">
        <h1 className="text-2xl font-bold text-foreground">Painel do Professor</h1>

        {/* Profile */}
        <Card className="p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <div className="size-14 rounded-full bg-primary/10 flex items-center justify-center">
                <GraduationCap className="size-7 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">{profile?.name ?? '—'}</h2>
                <p className="text-sm text-muted-foreground capitalize">{profile?.role ?? 'professor'}</p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => setPwOpen(true)} className="gap-2">
              <KeyRound className="size-4" /> Alterar palavra-passe
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
            <div className="flex items-center gap-3 rounded-lg border border-border p-4">
              <BookOpen className="size-5 text-primary shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Disciplinas</p>
                <p className="text-sm font-medium text-foreground">
                  {profile?.disciplines?.length ? profile.disciplines.join(', ') : '—'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg border border-border p-4">
              <Users className="size-5 text-primary shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Contextos que leciona</p>
                <p className="text-sm font-medium text-foreground">{profile?.contexts_count ?? 0}</p>
              </div>
            </div>
          </div>
        </Card>

        {/* WhatsApp status */}
        <Card className="p-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <Smartphone className="size-6 text-primary" />
              <div>
                <h2 className="text-base font-semibold text-foreground">Estado do WhatsApp</h2>
                <p className="text-sm">
                  {waChecking ? (
                    <span className="text-muted-foreground">A verificar…</span>
                  ) : waConnected ? (
                    <span className="text-success inline-flex items-center gap-1"><CheckCircle className="size-4" /> Conectado</span>
                  ) : (
                    <span className="text-destructive inline-flex items-center gap-1"><XCircle className="size-4" /> Desconectado</span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => void checkStatus()} className="gap-2">
                <RefreshCw className="size-4" /> Verificar
              </Button>
              {!waConnected && (
                <Button size="sm" onClick={openQr} className="gap-2">
                  <Smartphone className="size-4" /> Conectar
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* CSV templates */}
        <Card className="p-6">
          <h2 className="text-base font-semibold text-foreground mb-1">Modelos de CSV</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Descarregue os modelos com as colunas exactas, preencha com os dados reais e
            importe em <strong>Contextos</strong> (estudantes) e <strong>Notas</strong> (notas).
          </p>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => downloadCsv('modelo-estudantes.csv', STUDENTS_TEMPLATE)} className="gap-2">
              <Download className="size-4" /> Modelo de estudantes
            </Button>
            <Button variant="outline" onClick={() => downloadCsv('modelo-notas.csv', GRADES_TEMPLATE)} className="gap-2">
              <Download className="size-4" /> Modelo de notas
            </Button>
          </div>
        </Card>
      </main>

      {/* QR dialog */}
      <Dialog open={qrOpen} onOpenChange={(o) => { if (!o) closeQr() }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Conectar WhatsApp</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col items-center gap-3 py-2">
            <p className="text-sm text-muted-foreground text-center">
              Abre o WhatsApp → Definições → Aparelhos ligados → Ligar aparelho, e lê o código.
            </p>
            {qrLoading && <RefreshCw className="size-8 animate-spin text-primary" />}
            {qrCode && !qrLoading && (
              <img src={qrCode} alt="QR Code WhatsApp" className="size-56 rounded-lg border border-border" />
            )}
            {qrError && <p className="text-sm text-destructive text-center">{qrError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={closeQr}>Fechar</Button>
            <Button onClick={() => void fetchQr()} disabled={qrLoading} className="gap-2">
              <RefreshCw className="size-4" /> Novo código
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Change password dialog */}
      <Dialog open={pwOpen} onOpenChange={setPwOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Alterar palavra-passe</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="new-pw">Nova palavra-passe</Label>
              <Input id="new-pw" type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm-pw">Confirmar palavra-passe</Label>
              <Input id="confirm-pw" type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} />
            </div>
            <ul className="text-xs space-y-1">
              <li className={hasMinLen ? 'text-success' : 'text-muted-foreground'}>• Mínimo 8 caracteres</li>
              <li className={hasUpper ? 'text-success' : 'text-muted-foreground'}>• Pelo menos uma maiúscula</li>
              <li className={pwMatch ? 'text-success' : 'text-muted-foreground'}>• As palavras-passe coincidem</li>
            </ul>
            {pwError && <p role="alert" className="text-sm text-destructive">{pwError}</p>}
            {pwOk && <p className="text-sm text-success inline-flex items-center gap-1"><CheckCircle className="size-4" /> Palavra-passe alterada.</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPwOpen(false)} disabled={pwLoading}>Cancelar</Button>
            <Button onClick={submitPw} disabled={!canChangePw}>
              {pwLoading ? 'A guardar…' : 'Guardar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
