import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token, refresh_token: newRefreshToken } = response.data
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', newRefreshToken)

          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)

// API methods
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/api/auth/login', { email, password }),
  register: (data: { email: string; password: string; business_name: string }) =>
    api.post('/api/auth/register', data),
  me: () => api.get('/api/auth/me'),
  refresh: (refresh_token: string) =>
    api.post('/api/auth/refresh', { refresh_token }),
}

export const providerApi = {
  getStats: () => api.get('/api/provider/stats'),
  getSubscription: () => api.get('/api/provider/subscription'),
  createCheckoutSession: (plan: string) => api.post(`/api/provider/subscription/checkout?plan=${plan}`),
  upgradePlan: (plan: string) => api.post(`/api/provider/subscription/upgrade?plan=${plan}`),
  activateTrial: () => api.post('/api/provider/subscription/activate-trial'),
  updateSettings: (data: any) => api.put('/api/provider/settings', data),
}

export const bookingsApi = {
  list: (params?: { status_filter?: string; page?: number; size?: number }) =>
    api.get('/api/provider/bookings', { params }),
  getToday: () => api.get('/api/provider/bookings/today'),
  getUpcoming: (limit = 10) => api.get(`/api/provider/bookings/upcoming?limit=${limit}`),
  get: (id: string) => api.get(`/api/provider/bookings/${id}`),
  approve: (id: string, provider_notes?: string) =>
    api.post(`/api/provider/bookings/${id}/approve`, { provider_notes }),
  decline: (id: string, reason: string) =>
    api.post(`/api/provider/bookings/${id}/decline`, { reason }),
  arrive: (id: string) => api.post(`/api/provider/bookings/${id}/arrive`),
  complete: (id: string) => api.post(`/api/provider/bookings/${id}/complete`),
  cancel: (id: string, reason?: string) =>
    api.post(`/api/provider/bookings/${id}/cancel`, null, { params: { reason } }),
  confirmPayment: (id: string) => api.post(`/api/provider/bookings/${id}/confirm-payment`),
}

export const availabilityApi = {
  getWeekly: () => api.get('/api/provider/availability'),
  updateDay: (dayOfWeek: number, data: any) =>
    api.put(`/api/provider/availability/${dayOfWeek}`, data),
  bulkUpdate: (schedule: any[]) =>
    api.post('/api/provider/availability/bulk', schedule),
  reset: () => api.post('/api/provider/availability/reset'),
  getBlocked: () => api.get('/api/provider/availability/blocked'),
  addBlocked: (data: { date: string; reason?: string }) =>
    api.post('/api/provider/availability/blocked', data),
  removeBlocked: (id: string) =>
    api.delete(`/api/provider/availability/blocked/${id}`),
}

export const apiKeysApi = {
  list: () => api.get('/api/provider/apikeys'),
  create: (name?: string) => api.post('/api/provider/apikeys', { name }),
  get: (id: string) => api.get(`/api/provider/apikeys/${id}`),
  update: (id: string, data: { name?: string; is_active?: boolean }) =>
    api.patch(`/api/provider/apikeys/${id}`, data),
  revoke: (id: string) => api.delete(`/api/provider/apikeys/${id}`),
  regenerate: (id: string) => api.post(`/api/provider/apikeys/${id}/regenerate`),
}

export const publicApi = {
  verifyBooking: (token: string) =>
    api.get(`/api/bookings/verify/${token}`),
}

export const adminApi = {
  getStats: () => api.get('/api/admin/stats'),
  getUsers: (params?: { page?: number; size?: number; search?: string; is_active?: boolean }) =>
    api.get('/api/admin/users', { params }),
  getUser: (userId: string) => api.get(`/api/admin/users/${userId}`),
  toggleUserActive: (userId: string, isActive: boolean) =>
    api.patch(`/api/admin/users/${userId}/activate?is_active=${isActive}`),
  updateUserSubscription: (userId: string, planType: string, status: string) =>
    api.patch(`/api/admin/users/${userId}/subscription?plan_type=${planType}&subscription_status=${status}`),
  getBookings: (params?: { page?: number; size?: number; user_id?: string }) =>
    api.get('/api/admin/bookings', { params }),
  getHealth: () => api.get('/api/admin/health'),
}

