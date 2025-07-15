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

    async addDomain(domain: string, regionId: string) {
        return this.client.post('/domains/', {
            domain,
            region_id: regionId
        })
    }

    async updateDomain(domainId: string, data: {
        domain: string
        region_id: string
        is_verified: boolean
    }) {
        return this.client.put(`/domains/${domainId}`, data)
    }

    async deleteDomain(domainId: string) {
        return this.client.delete(`/domains/${domainId}`)
    }

    // async getRegions() {
    //     return this.client.get('/domains/regions')
    // }

    /**
     * Поиск регионов по названию или коду
     */
    async searchRegions(query: string, limit = 20) {
        return this.client.get('/domains/regions/search', {
            params: {
                q: query,
                limit
            }
        })
    }

    /**
     * Получение всех регионов (существующий метод)
     */
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
    /**
     * Загрузка ключевых слов из текстового файла
     */
    async loadKeywordsFromTextFile(url: string) {
        return this.client.post('/domains/load-keywords/text-file', {
            url
        })
    }

    /**
     * Загрузка ключевых слов из Excel файла
     */
    async loadKeywordsFromExcel(url: string, sheet: number = 1, startRow: number = 1) {
        return this.client.post('/domains/load-keywords/excel', {
            url,
            sheet,
            start_row: startRow
        })
    }

    /**
     * Загрузка ключевых слов из Word документа
     */
    async loadKeywordsFromWord(url: string) {
        return this.client.post('/domains/load-keywords/word', {
            url
        })
    }

    /**
     * Обновление ключевого слова
     */
    async updateKeyword(keywordId: string, data: {
        keyword: string,
        region_id: string,
        device_type: string,
        check_frequency: string,
        is_active: boolean
    }) {
        return this.client.put(`/domains/keywords/${keywordId}`, data)
    }

    /**
     * Удаление ключевого слова
     */
    async deleteKeyword(keywordId: string) {
        return this.client.delete(`/domains/keywords/${keywordId}`)
    }

    /**
     * Массовое удаление ключевых слов
     */
    async bulkDeleteKeywords(keywordIds: string[]) {
        return this.client.delete('/domains/keywords/bulk', {
            data: {
                keyword_ids: keywordIds
            }
        })
    }

    /**
     * Массовое редактирование ключевых слов
     */
    async bulkEditKeywords(domainId: string, data: {
        added_keywords: string[],
        removed_keywords: string[],
        new_keywords_settings?: {
            region_id: string,
            device_type: string,
            check_frequency: string,
            is_active: boolean
        }
    }) {
        return this.client.post(`/domains/${domainId}/keywords/bulk-edit`, data)
    }


    /**
     * Массовое добавление ключевых слов
     */
    async addBulkKeywords(
        domainId: string,
        keywords: string[],
        regionId: string,
        deviceType: string = 'DESKTOP',
        checkFrequency: string = 'daily',
        isActive: boolean = true
    ) {
        return this.client.post(`/domains/${domainId}/keywords/bulk`, {
            keywords,
            region_id: regionId,
            device_type: deviceType,
            check_frequency: checkFrequency,
            is_active: isActive
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

    // Strategy data import methods
    async importDataFromUrl(url: string) {
        return this.client.post('/strategies/import/url', {url})
    }

    async importDataFromGoogleSheets(url: string) {
        return this.client.post('/strategies/import/google-sheets', {url})
    }

    async importDataFromGoogleDocs(url: string) {
        return this.client.post('/strategies/import/google-docs', {url})
    }

    async validateDataSource(sourceData: {
        source_type: string
        source_url?: string
        data_content?: string
    }) {
        return this.client.post('/strategies/validate-data-source', sourceData)
    }

    // Strategy templates and execution methods
    async getStrategyTemplates(strategyType?: string) {
        const params = strategyType ? {strategy_type: strategyType} : {}
        return this.client.get('/strategies/templates', {params})
    }

    async createStrategy(strategyData: {
        template_id?: string
        name: string
        strategy_type: 'warmup' | 'position_check' | 'profile_nurture'
        config: Record<string, any>
    }) {
        return this.client.post('/strategies', strategyData)
    }

    async createTemporaryStrategy(strategyData: {
        name: string
        strategy_type: 'warmup' | 'position_check' | 'profile_nurture'
        config: Record<string, any>
        temporary?: boolean
    }) {
        return this.client.post('/strategies/temporary', {...strategyData, temporary: true})
    }

    async getStrategies(strategyType?: string) {
        const params = strategyType ? {strategy_type: strategyType} : {}
        return this.client.get('/strategies', {params})
    }

    async updateStrategy(strategyId: string, updateData: {
        name?: string
        config?: Record<string, any>
        is_active?: boolean
    }) {
        return this.client.put(`/strategies/${strategyId}`, updateData)
    }

    async deleteStrategy(strategyId: string) {
        return this.client.delete(`/strategies/${strategyId}`)
    }

    async executeStrategy(strategyId: string, executionParams: Record<string, any> = {}) {
        return this.client.post(`/strategies/${strategyId}/execute`, {
            execution_params: executionParams
        })
    }

    // Profile nurture specific methods
    async getAvailableSearchEngines() {
        return this.client.get('/strategies/profile-nurture/search-engines')
    }

    async validateProfileNurtureConfig(config: Record<string, any>) {
        return this.client.post('/strategies/profile-nurture/validate-config', config)
    }

    async testQuerySource(strategyId: string, sourceData: {
        source_type: string
        source_url?: string
        data_content?: string
    }) {
        return this.client.post(`/strategies/${strategyId}/test-query-source`, sourceData)
    }

    async getNurtureProgress(strategyId: string) {
        return this.client.get(`/strategies/${strategyId}/nurture-progress`)
    }

    async getStrategyExecutions(strategyId?: string) {
        const params = strategyId ? {strategy_id: strategyId} : {}
        return this.client.get('/strategies/executions', {params})
    }

    // Data source management
    async addDataSource(strategyId: string, sourceData: {
        source_type: string
        source_url?: string
        data_content?: string
    }) {
        return this.client.post(`/strategies/${strategyId}/data-sources`, sourceData)
    }

    async uploadDataFile(strategyId: string, file: File) {
        const formData = new FormData()
        formData.append('file', file)
        return this.client.post(`/strategies/${strategyId}/data-sources/upload-file`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
    }

    async getDataSourcePreview(sourceData: {
        source_type: string
        source_url?: string
        data_content?: string
    }) {
        return this.client.post('/strategies/data-sources/preview', sourceData)
    }

    // Project strategy assignment
    async assignStrategiesToProject(assignment: {
        domain_id?: string
        warmup_strategy_id?: string
        position_check_strategy_id?: string
        profile_nurture_strategy_id?: string
    }) {
        return this.client.post('/strategies/project-strategies', assignment)
    }

    async getProjectStrategies(domainId?: string) {
        const params = domainId ? {domain_id: domainId} : {}
        return this.client.get('/strategies/project-strategies', {params})
    }

    async updateProjectStrategy(assignmentId: string, updateData: {
        warmup_strategy_id?: string
        position_check_strategy_id?: string
        profile_nurture_strategy_id?: string
    }) {
        return this.client.put(`/strategies/project-strategies/${assignmentId}`, updateData)
    }

    async deleteProjectStrategy(assignmentId: string) {
        return this.client.delete(`/strategies/project-strategies/${assignmentId}`)
    }

    // Strategy analytics and reporting
    async getStrategyAnalytics(strategyIds: string[], dateFrom?: string, dateTo?: string) {
        return this.client.post('/strategies/analytics', {
            strategy_ids: strategyIds,
            date_from: dateFrom,
            date_to: dateTo
        })
    }

    async getStrategyStats(strategyId: string) {
        return this.client.get(`/strategies/${strategyId}/stats`)
    }

    async getStrategyExecutionHistory(strategyId: string, limit = 50, offset = 0) {
        return this.client.get(`/strategies/${strategyId}/executions`, {
            params: {limit, offset}
        })
    }

    // Default configurations
    async getDefaultConfigs() {
        return this.client.get('/strategies/default-configs')
    }

    async getStrategyDefaults(strategyType: string) {
        return this.client.get(`/strategies/defaults/${strategyType}`)
    }

    // Validation and testing
    async validateStrategyConfig(strategyType: string, config: Record<string, any>) {
        return this.client.post('/strategies/validate-config', {
            strategy_type: strategyType,
            config
        })
    }

    async testUrlEndpoint(url: string) {
        return this.client.post('/strategies/test-url-endpoint', {url})
    }

    async testGoogleSheetsAccess(url: string) {
        return this.client.post('/strategies/test-google-sheets', {url})
    }

    async testGoogleDocsAccess(url: string) {
        return this.client.post('/strategies/test-google-docs', {url})
    }
}

export const api = new ApiClient()
