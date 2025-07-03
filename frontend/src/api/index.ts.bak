import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor для добавления токена
    this.client.interceptors.request.use(
      (config) => {
        const authStore = useAuthStore()
        if (authStore.token) {
          config.headers.Authorization = `Bearer ${authStore.token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor для обработки ошибок
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const authStore = useAuthStore()

          // Пытаемся обновить токен
          if (authStore.refreshToken) {
            try {
              await authStore.refreshAccessToken()
              // Повторяем запрос с новым токеном
              const config = error.config
              config.headers.Authorization = `Bearer ${authStore.token}`
              return this.client.request(config)
            } catch (refreshError) {
              authStore.logout()
              window.location.href = '/login'
            }
          } else {
            authStore.logout()
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth endpoints
  async register(email: string, password: string) {
    return this.client.post('/auth/register', { email, password })
  }

  async login(email: string, password: string) {
    return this.client.post('/auth/login', { email, password })
  }

  async refreshToken(refreshToken: string) {
    return this.client.post('/auth/refresh', { refresh_token: refreshToken })
  }

  async getProfile() {
    return this.client.get('/auth/profile')
  }

  async changePassword(currentPassword: string, newPassword: string) {
    return this.client.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    })
  }

  async regenerateApiKey() {
    return this.client.post('/auth/regenerate-api-key')
  }

  // Domains endpoints
  async getDomains() {
    return this.client.get('/domains/')
  }

  async addDomain(domain: string) {
    return this.client.post('/domains/', { domain })
  }

  async deleteDomain(domainId: string) {
    return this.client.delete(`/domains/${domainId}`)
  }

  async getRegions() {
    return this.client.get('/domains/regions')
  }

  async getDomainKeywords(domainId: string) {
    return this.client.get(`/domains/${domainId}/keywords`)
  }

  async addKeyword(domainId: string, keyword: string, regionId: string, deviceType: string) {
    return this.client.post(`/domains/${domainId}/keywords`, {
      keyword,
      region_id: regionId,
      device_type: deviceType
    })
  }

  async deleteKeyword(keywordId: string) {
    return this.client.delete(`/domains/keywords/${keywordId}`)
  }

  // Billing endpoints
  async getBalance() {
    return this.client.get('/billing/balance')
  }

  async topupBalance(amount: number) {
    return this.client.post('/billing/topup', { amount })
  }

  async getCurrentTariff() {
    return this.client.get('/billing/tariff')
  }

  async getTransactionHistory(limit = 50, offset = 0) {
    return this.client.get('/billing/transactions', {
      params: { limit, offset }
    })
  }

  async calculateCheckCost(checksCount = 1) {
    return this.client.get('/billing/check-cost', {
      params: { checks_count: checksCount }
    })
  }

  // Tasks endpoints
  async createParseTask(keyword: string, deviceType: string, pages = 10, regionCode = '213') {
    return this.client.post('/tasks/parse', {
      keyword,
      device_type: deviceType,
      pages,
      region_code: regionCode
    })
  }

  async createPositionCheckTask(keywordIds: string[], deviceType: string) {
    return this.client.post('/tasks/check-positions', {
      keyword_ids: keywordIds,
      device_type: deviceType
    })
  }

  async getTaskStatus(taskId: string) {
    return this.client.get(`/tasks/status/${taskId}`)
  }

  async getUserTasks(limit = 50, offset = 0, status?: string) {
    return this.client.get('/tasks/my-tasks', {
      params: { limit, offset, ...(status && { status }) }
    })
  }
}

export const api = new ApiClient()
