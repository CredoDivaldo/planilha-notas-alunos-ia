export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  // In production the frontend is served by the same FastAPI server, so use
  // relative paths. In local dev, Vite proxies /api/* to localhost:8000.
  const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
  const stored = localStorage.getItem('auth_user')
  const token: string | null = stored
    ? (JSON.parse(stored) as { token: string }).token
    : null

  const res = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText })) as { detail?: string }
    throw new Error(err.detail ?? `Request failed: ${res.status}`)
  }

  if (res.status === 204) {
    return undefined as unknown as T
  }

  return res.json() as Promise<T>
}
