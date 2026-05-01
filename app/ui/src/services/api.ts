import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || '/api/v1'

export const api = axios.create({ baseURL: BASE, timeout: 60000 })

// Attach JWT from localStorage if present
api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('capmarkets_token')
  if (token) cfg.headers['Authorization'] = `Bearer ${token}`
  return cfg
})
