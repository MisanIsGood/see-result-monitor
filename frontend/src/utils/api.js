import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor: unwrap data, surface errors
api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'Something went wrong'
    return Promise.reject(new Error(msg))
  }
)

export const registrationsApi = {
  create: (data) => api.post('/registrations/', data),
  list: () => api.get('/registrations/'),
  getById: (id) => api.get(`/registrations/${id}`),
  cancel: (id) => api.delete(`/registrations/${id}`),
}

export const monitorApi = {
  status: () => api.get('/monitor/status'),
  start: () => api.post('/monitor/start'),
  stop: () => api.post('/monitor/stop'),
}

export const logsApi = {
  list: (params) => api.get('/logs/', { params }),
}

export default api
