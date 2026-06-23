// apiFetch é a função central que TODO o frontend usa para falar com o backend.
// Junta o endereço, anexa o token de autenticação e trata os erros num só sítio.
// (O equivalente em Python seria um wrapper à volta do `requests`/`httpx`.)
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  // Em produção o frontend e a API estão no mesmo servidor (caminho relativo);
  // em desenvolvimento o Vite reencaminha /api/* para localhost:8000.
  const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
  // Lê o utilizador guardado no navegador (localStorage) para obter o token.
  const stored = localStorage.getItem('auth_user')
  const token: string | null = stored
    ? (JSON.parse(stored) as { token: string }).token
    : null

  // Don't set Content-Type for FormData — browser must set it with the multipart boundary
  const isFormData = options.body instanceof FormData
  // Faz o pedido HTTP (await espera pela resposta). Os cabeçalhos incluem o
  // Content-Type (excepto em uploads de ficheiro) e o token "Bearer", se existir.
  const res = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  // Se a resposta não for "ok" (código de erro), trata-o aqui de forma central.
  if (!res.ok) {
    if (res.status === 401) {  // 401 = não autenticado → volta ao login
      // Only redirect when there was a stored session and we're not already on /login
      const hadToken = !!localStorage.getItem('auth_user')
      localStorage.removeItem('auth_user')
      if (hadToken && !window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
      throw new Error('Sessão expirada. Volta a fazer login.')
    }
    const err = await res.json().catch(() => ({ detail: res.statusText })) as { detail?: unknown }
    const detail = err.detail
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((e: { msg?: string }) => e?.msg ?? JSON.stringify(e)).join('; ')
        : `Request failed: ${res.status}`
    throw new Error(message)
  }

  // 204 = sucesso "sem conteúdo" (ex.: apagar algo): não há JSON para devolver.
  if (res.status === 204) {
    return undefined as unknown as T
  }

  // Caso normal: converte a resposta de JSON para objecto e devolve-o.
  return res.json() as Promise<T>
}
