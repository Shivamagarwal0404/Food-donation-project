/**
 * FoodShare — API Services
 * Provides centralized, typed Axios client methods for FoodShare backend endpoints.
 */
import axios from 'axios'
import type {
  FoodCategory,
  FoodDonation,
  DonationRequest,
  Pickup,
  PlatformImpact,
  User,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach JWT access token if available in localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('foodshare_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 Unauthorized responses gracefully
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthEndpoint = error.config?.url?.includes('/auth/token/')
    if (error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('foodshare_access_token')
      localStorage.removeItem('foodshare_refresh_token')
      localStorage.removeItem('foodshare_user')
      window.dispatchEvent(new Event('foodshare_auth_logout'))
    }
    return Promise.reject(error)
  }
)

export const authService = {
  login: async (
    email: string,
    password: string
  ): Promise<{ login_otp_required: boolean; email: string; message: string }> => {
    const res = await apiClient.post('/auth/token/', { email, password })
    return res.data
  },

  verifyLoginOtp: async (
    email: string,
    otp: string
  ): Promise<{ message: string; access?: string; refresh?: string; tokens?: { access: string; refresh: string }; user?: User }> => {
    const res = await apiClient.post('/auth/login-otp/verify/', { email, otp })
    if (res.data.tokens?.access || res.data.access) {
      const access = res.data.access || res.data.tokens?.access
      const refresh = res.data.refresh || res.data.tokens?.refresh
      localStorage.setItem('foodshare_access_token', access)
      localStorage.setItem('foodshare_refresh_token', refresh)
    }
    if (res.data.user) {
      localStorage.setItem('foodshare_user', JSON.stringify(res.data.user))
    }
    window.dispatchEvent(new Event('foodshare_auth_change'))
    return res.data
  },

  resendLoginOtp: async (email: string): Promise<{ message: string }> => {
    const res = await apiClient.post('/auth/login-otp/resend/', { email })
    return res.data
  },

  register: async (data: Record<string, unknown>): Promise<{ tokens?: { access: string; refresh: string }; user: User; message?: string }> => {
    const res = await apiClient.post('/users/register/', data)
    return res.data
  },

  verifyOtp: async (
    email: string,
    otp: string
  ): Promise<{ message: string; tokens?: { access: string; refresh: string }; user?: User }> => {
    const res = await apiClient.post('/users/verify-otp/', { email, otp })
    return res.data
  },

  resendOtp: async (email: string): Promise<{ message: string }> => {
    const res = await apiClient.post('/users/resend-otp/', { email })
    return res.data
  },

  requestPasswordReset: async (email: string): Promise<{ message: string; email: string }> => {
    const res = await apiClient.post('/users/password-reset/request/', { email })
    return res.data
  },

  confirmPasswordReset: async (data: {
    email: string
    otp: string
    new_password: string
    new_password_confirm: string
  }): Promise<{ message: string }> => {
    const res = await apiClient.post('/users/password-reset/confirm/', data)
    return res.data
  },

  resendPasswordReset: async (email: string): Promise<{ message: string }> => {
    const res = await apiClient.post('/users/password-reset/resend/', { email })
    return res.data
  },

  setSession: (tokens: { access: string; refresh: string }, user: User) => {
    if (tokens?.access) {
      localStorage.setItem('foodshare_access_token', tokens.access)
      localStorage.setItem('foodshare_refresh_token', tokens.refresh)
    }
    localStorage.setItem('foodshare_user', JSON.stringify(user))
    window.dispatchEvent(new Event('foodshare_auth_change'))
  },

  logout: () => {
    localStorage.removeItem('foodshare_access_token')
    localStorage.removeItem('foodshare_refresh_token')
    localStorage.removeItem('foodshare_user')

    window.dispatchEvent(new Event('foodshare_auth_logout'))
  },

  getCurrentUser: async (): Promise<User> => {
    const res = await apiClient.get<User>('/users/me/')
    return res.data
  },

  getStoredUser: (): User | null => {
    const data = localStorage.getItem('foodshare_user')
    if (!data) return null
    try {
      return JSON.parse(data)
    } catch {
      return null
    }
  },
}

export const donationService = {
  getCategories: async (): Promise<FoodCategory[]> => {
    const res = await apiClient.get<any>('/donations/categories/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },

  createCategory: async (data: { name: string; description?: string; icon?: string; is_active?: boolean }): Promise<FoodCategory> => {
    const res = await apiClient.post<FoodCategory>('/donations/categories/', data)
    return res.data
  },

  updateCategory: async (id: number, data: Partial<FoodCategory>): Promise<FoodCategory> => {
    const res = await apiClient.patch<FoodCategory>(`/donations/categories/${id}/`, data)
    return res.data
  },

  getDonations: async (params?: Record<string, string | number>): Promise<FoodDonation[]> => {
    const res = await apiClient.get<any>('/donations/', { params })
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },

  getDonationDetail: async (id: number): Promise<FoodDonation> => {
    const res = await apiClient.get<FoodDonation>(`/donations/${id}/`)
    return res.data
  },

  createDonation: async (data: Partial<FoodDonation>): Promise<FoodDonation> => {
    const res = await apiClient.post<FoodDonation>('/donations/', data)
    return res.data
  },

  cancelDonation: async (id: number) => {
    const res = await apiClient.post(`/donations/${id}/cancel/`)
    return res.data
  },

  getRequests: async (params?: Record<string, string | number>): Promise<DonationRequest[]> => {
    const res = await apiClient.get<any>('/donations/requests/', { params })
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },

  getMyDonations: async (): Promise<FoodDonation[]> => {
    const res = await apiClient.get<any>('/donations/my-donations/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },

  getMyRequests: async (): Promise<DonationRequest[]> => {
    const res = await apiClient.get<any>('/donations/my-requests/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },

  requestDonation: async (donationId: number, requestedServings: number, message: string): Promise<DonationRequest> => {
    const res = await apiClient.post<DonationRequest>('/donations/requests/', {
      donation: donationId,
      requested_servings: requestedServings,
      message,
    })
    return res.data
  },

  acceptRequest: async (requestId: number) => {
    const res = await apiClient.post(`/donations/requests/${requestId}/accept/`)
    return res.data
  },

  rejectRequest: async (requestId: number) => {
    const res = await apiClient.post(`/donations/requests/${requestId}/reject/`)
    return res.data
  },

  cancelRequest: async (requestId: number) => {
    const res = await apiClient.post(`/donations/requests/${requestId}/cancel/`)
    return res.data
  },
}

export const pickupService = {
  getPickups: async (params?: Record<string, string | number>): Promise<Pickup[]> => {
    const res = await apiClient.get<any>('/pickups/', { params })
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },

  getPickupDetail: async (id: number): Promise<Pickup> => {
    const res = await apiClient.get<Pickup>(`/pickups/${id}/`)
    return res.data
  },

  getAvailablePickups: async (): Promise<Pickup[]> => {
    const res = await apiClient.get<any>('/pickups/available/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },

  getMyPickups: async (): Promise<Pickup[]> => {
    const res = await apiClient.get<any>('/pickups/my-pickups/')
    return Array.isArray(res.data) ? res.data : (res.data?.results || [])
  },

  claimPickup: async (pickupId: number) => {
    const res = await apiClient.post(`/pickups/${pickupId}/assign/`)
    return res.data
  },

  markPickedUp: async (pickupId: number) => {
    const res = await apiClient.post(`/pickups/${pickupId}/pickup/`)
    return res.data
  },

  markDelivered: async (pickupId: number) => {
    const res = await apiClient.post(`/pickups/${pickupId}/deliver/`)
    return res.data
  },

  markCompleted: async (pickupId: number) => {
    const res = await apiClient.post(`/pickups/${pickupId}/complete/`)
    return res.data
  },

  updatePickupStatus: async (pickupId: number, status: 'PICKED_UP' | 'DELIVERED' | 'COMPLETED') => {
    const res = await apiClient.post(`/pickups/${pickupId}/status/`, { status })
    return res.data
  },
}

export const analyticsService = {
  getImpactMetrics: async (): Promise<PlatformImpact> => {
    const res = await apiClient.get<PlatformImpact>('/analytics/impact/')
    return res.data
  },
}
