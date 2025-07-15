// frontend/src/api/index.ts
import axios, {type AxiosInstance} from 'axios'
import {useAuthStore} from '@/stores/auth'

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

    // Стандартные HTTP методы
    async get(url: string, config?: any) {
        return this.client.get(url, config)
    }

    async post(url: string, data?: any, config?: any) {
        return this.client.post(url, data, config)
    }

    async put(url: string, data?: any, config?: any) {
        return this.client.put(url, data, config)
    }

    async patch(url: string, data?: any, config?: any) {
        return this.client.patch(url, data, config)
    }

    async delete(url: string, config?: any) {
        return this.client.delete(url, config)
    }

    async head(url: string, config?: any) {
        return this.client.head(url, config)
    }

    async options(url: string, config?: any) {
        return this.client.options(url, config)
    }

    // Удобные методы с параметрами
    async getWithParams(url: string, params: Record<string, any>, config?: any) {
        return this.client.get(url, {...config, params})
    }

    async postFormData(url: string, formData: FormData, config?: any) {
        return this.client.post(url, formData, {
            ...config,
            headers: {
                ...config?.headers,
                'Content-Type': 'multipart/form-data'
            }
        })
    }

    // Auth endpoints
    async register(email: string, password: string) {
        return this.client.post('/auth/register', {email, password})
    }

    async login(email: string, password: string) {
        return this.client.post('/auth/login', {email, password})
    }

    async refreshToken(refreshToken: string) {
        return this.client.post('/auth/refresh', {refresh_token: refreshToken})
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
        return this.client.post('/domains/', {domain})
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
        return this.client.post('/billing/topup', {amount})
    }

    // Временно отключен до исправления backend
    async getCurrentTariff() {
        // return this.client.get('/billing/tariff')
        return Promise.resolve({
            data: {
                id: '1',
                name: 'Premium',
                description: 'Премиум тариф',
                cost_per_check: 0.80,
                min_monthly_topup: 20000.00,
                server_binding_allowed: true,
                priority_level: 10
            }
        })
    }

    async getTransactionHistory(limit = 50, offset = 0) {
        return this.client.get('/billing/transactions', {
            params: {limit, offset}
        })
    }

    async calculateCheckCost(checksCount = 1) {
        return this.client.get('/billing/check-cost', {
            params: {checks_count: checksCount}
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
            params: {limit, offset, ...(status && {status})}
        })
    }

    // Bulk keyword methods
    async loadKeywordsFromTextFile(url: string) {
        return this.client.post('/domains/keywords/load-from-text', {url})
    }

    async loadKeywordsFromExcel(url: string, sheet: number = 1, startRow: number = 1) {
        return this.client.post('/domains/keywords/load-from-excel', {
            url,
            sheet,
            start_row: startRow
        })
    }

    async loadKeywordsFromWord(url: string) {
        return this.client.post('/domains/keywords/load-from-word', {url})
    }

    async addBulkKeywords(domainId: string, keywords: string[], regionId: string, deviceType: string) {
        return this.client.post(`/domains/${domainId}/keywords/bulk`, {
            keywords,
            region_id: regionId,
            device_type: deviceType
        })
    }

    // Proxy endpoints
    async getDomainProxies(domainId: string) {
        return this.client.get(`/proxies/domain/${domainId}`)
    }

    async getDomainProxySettings(domainId: string) {
        return this.client.get(`/domains/${domainId}/proxy-settings`)
    }

    async updateDomainProxySettings(domainId: string, settings: any) {
        return this.client.put(`/domains/${domainId}/proxy-settings`, {settings})
    }

    async createWarmupTask(deviceType: string = 'desktop', profileId?: string, priority: number = 2) {
        return this.client.post('/tasks/warmup', {
            device_type: deviceType,
            ...(profileId && {profile_id: profileId}),
            priority
        })
    }

    // Admin Debug endpoints
    async getAdminTasks(limit = 50, offset = 0, status?: string) {
        return this.client.get('/admin/debug/tasks', {  // ← ИЗМЕНИТЬ с /admin/tasks на /admin/debug/tasks
            params: {limit, offset, ...(status && {status})}
        })
    }

    async getDebugSessions() {
        return this.client.get('/admin/debug/sessions')
    }

    async startDebugSession(taskId: string, deviceType: string = 'desktop') {
        return this.client.post(`/admin/debug/start/${taskId}`, {
            device_type: deviceType
        })
    }

    async stopDebugSession(taskId: string) {
        return this.client.post(`/admin/debug/stop/${taskId}`)
    }

    async getVncInstructions(taskId: string) {
        return this.client.get(`/admin/debug/vnc-instructions/${taskId}`)
    }

    async getDebugSessionStatus(taskId: string) {
        return this.client.get(`/admin/debug/session/${taskId}`)
    }

    async getDebugScreenshot(taskId: string) {
        return this.client.get(`/admin/debug/screenshot/${taskId}`, {
            responseType: 'blob'
        })
    }

    async getDebugSessionLogs(taskId: string, limit = 100) {
        return this.client.get(`/admin/debug/logs/${taskId}`, {
            params: {limit}
        })
    }
}

export const api = new ApiClient()
