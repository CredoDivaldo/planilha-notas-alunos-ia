export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  // In production the frontend is served by the same FastAPI server, so use
  // relative paths. In local dev, Vite proxies /api/* to localhost:8000.
  const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
  const stored = localStorage.getItem('auth_user')
  const token: string | null = stored
    ? (JSON.parse(stored) as { token: string }).token
    : null

  // Don't set Content-Type for FormData — browser must set it with the multipart boundary
  const isFormData = options.body instanceof FormData
  const res = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (!res.ok) {
    if (res.status === 401) {
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

  if (res.status === 204) {
    return undefined as unknown as T
  }

  return res.json() as Promise<T>
}
