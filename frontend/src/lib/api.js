// When the API is hosted separately (e.g. frontend on Vercel, API on Oracle
// VM), set VITE_API_URL=https://api.example.com in frontend/.env.production.
// Same-origin deploys (Flask serves dist/) leave it unset.
const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
export const apiUrl = (path) => `${API_BASE}${path}`

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

export async function api(path, { method = 'GET', body, formData } = {}) {
  const opts = {
    method,
    credentials: 'include',
    headers: {},
  }
  if (formData) {
    opts.body = formData
  } else if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }

  const res = await fetch(`${API_BASE}${path}`, opts)
  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { error: text }
    }
  }

  if (!res.ok) {
    throw new ApiError(
      (data && (data.error || data.message)) || `Request failed (${res.status})`,
      res.status,
      data
    )
  }
  return data
}

export const get = (path) => api(path)
export const post = (path, body) => api(path, { method: 'POST', body })
export const postForm = (path, formData) => api(path, { method: 'POST', formData })
