const API_BASE = import.meta.env.VITE_API_URL || '/api'

function getToken() {
  return localStorage.getItem('token')
}

async function request(path, options = {}) {
  const headers = { ...options.headers }
  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(options.body)
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    const err = new Error(data.error || 'Request failed')
    err.status = res.status
    throw err
  }

  return data
}

export const api = {
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: { email, password } }),

  me: () => request('/auth/me'),

  listDocuments: () => request('/documents'),

  getDocument: (id) => request(`/documents/${id}`),

  createDocument: (title, content) =>
    request('/documents', { method: 'POST', body: { title, content } }),

  updateDocument: (id, data) =>
    request(`/documents/${id}`, { method: 'PUT', body: data }),

  deleteDocument: (id) =>
    request(`/documents/${id}`, { method: 'DELETE' }),

  listUsers: () => request('/users'),

  shareDocument: (docId, userId, permission) =>
    request(`/documents/${docId}/share`, {
      method: 'POST',
      body: { user_id: userId, permission },
    }),

  unshareDocument: (docId, userId) =>
    request(`/documents/${docId}/share/${userId}`, { method: 'DELETE' }),

  importDocument: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/documents/import', { method: 'POST', body: form })
  },

  attachFile: (docId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/documents/${docId}/attachments`, { method: 'POST', body: form })
  },
}
