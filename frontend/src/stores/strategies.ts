// frontend/src/stores/strategies.ts
import {defineStore} from 'pinia'
import {ref, computed} from 'vue'
import {api} from '@/api'

export interface Strategy {
    id: string
    user_id: string
    template_id?: string
    name: string
    strategy_type: 'warmup' | 'position_check' | 'profile_nurture'
    config: Record<string, any>
    created_at: string
    updated_at: string
    is_active: boolean
    data_sources: DataSource[]
}

export interface DataSource {
    id: string
    strategy_id: string
    source_type: 'manual_list' | 'file_upload' | 'url_import' | 'google_sheets' | 'google_docs'
    source_url?: string
    file_path?: string
    items_count: number
    is_active: boolean
    created_at: string
}

export interface StrategyTemplate {
    id: string
    name: string
    description?: string
    strategy_type: 'warmup' | 'position_check' | 'profile_nurture'
    config: Record<string, any>
    is_system: boolean
    created_at: string
}

export interface StrategyExecution {
    id: string
    strategy_id: string
    task_id?: string
    execution_type: 'warmup' | 'position_check' | 'profile_nurture'
    profile_id?: string
    parameters?: Record<string, any>
    result?: Record<string, any>
    status: 'pending' | 'running' | 'completed' | 'failed'
    started_at?: string
    completed_at?: string
    error_message?: string
}

export const useStrategiesStore = defineStore('strategies', () => {
    const strategies = ref<Strategy[]>([])
    const templates = ref<StrategyTemplate[]>([])
    const executions = ref<StrategyExecution[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)

    // Computed getters
    const warmupStrategies = computed(() =>
        strategies.value.filter(s => s.strategy_type === 'warmup')
    )

    const positionCheckStrategies = computed(() =>
        strategies.value.filter(s => s.strategy_type === 'position_check')
    )

    const warmupTemplates = computed(() =>
        templates.value.filter(t => t.strategy_type === 'warmup')
    )

    const positionCheckTemplates = computed(() =>
        templates.value.filter(t => t.strategy_type === 'position_check')
    )

    const profileNurtureStrategies = computed(() =>
        strategies.value.filter(s => s.strategy_type === 'profile_nurture')
    )

    const profileNurtureTemplates = computed(() =>
        templates.value.filter(t => t.strategy_type === 'profile_nurture')
    )

    // Default configurations
    function getDefaultWarmupConfig() {
        return {
            type: 'mixed',
            proportions: {
                direct_visits: 30,
                search_visits: 70
            },
            min_sites: 3,
            max_sites: 7,
            session_timeout: 15,
            yandex_domain: 'yandex.ru',
            device_type: 'desktop'
        }
    }

    function getDefaultPositionCheckConfig() {
        return {
            check_frequency: 'daily',
            yandex_domain: 'yandex.ru',
            device_type: 'desktop',
            max_pages: 10,
            custom_schedule: null,
            behavior: {
                random_delays: true,
                scroll_pages: true,
                human_like_clicks: true
            }
        }
    }

    function getDefaultProfileNurtureConfig() {
        return {
            nurture_type: 'search_based',
            target_cookies: {
                min: 50,
                max: 100
            },
            session_config: {
                timeout_per_site: 15,
                min_timeout: 10,
                max_timeout: 30
            },
            search_engines: ['yandex.ru'],
            queries_source: {
                type: 'manual_input',
                refresh_on_each_cycle: false
            },
            behavior: {
                return_to_search: true,
                close_browser_after_cycle: false,
                emulate_human_actions: true,
                scroll_pages: true,
                random_clicks: true
            },
            proportions: {
                search_visits: 70,
                direct_visits: 30
            }
        }
    }

    // API methods
    async function fetchStrategyTemplates(strategyType?: string) {
        try {
            loading.value = true
            error.value = null

            const params = strategyType ? {strategy_type: strategyType} : {}
            const response = await api.get('/strategies/templates', {params})
            templates.value = response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка загрузки шаблонов стратегий'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function fetchStrategies(strategyType?: string) {
        try {
            loading.value = true
            error.value = null

            const params = strategyType ? {strategy_type: strategyType} : {}
            const response = await api.get('/strategies', {params})
            strategies.value = response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка загрузки стратегий'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function createStrategy(strategyData: {
        template_id?: string
        name: string
        strategy_type: 'warmup' | 'position_check' | 'profile_nurture'
        config: Record<string, any>
    }) {
        try {
            loading.value = true
            error.value = null

            const response = await api.post('/strategies', strategyData)
            strategies.value.push(response.data)

            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка создания стратегии'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function updateStrategy(strategyId: string, updateData: {
        name?: string
        config?: Record<string, any>
        is_active?: boolean
    }) {
        try {
            loading.value = true
            error.value = null

            const response = await api.put(`/strategies/${strategyId}`, updateData)

            // Обновляем стратегию в локальном состоянии
            const index = strategies.value.findIndex(s => s.id === strategyId)
            if (index !== -1) {
                strategies.value[index] = {...strategies.value[index], ...response.data}
            }

            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка обновления стратегии'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function deleteStrategy(strategyId: string) {
        try {
            loading.value = true
            error.value = null

            await api.delete(`/strategies/${strategyId}`)

            // Удаляем стратегию из локального состояния
            const index = strategies.value.findIndex(s => s.id === strategyId)
            if (index !== -1) {
                strategies.value.splice(index, 1)
            }
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка удаления стратегии'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function addDataSource(strategyId: string, sourceData: {
        source_type: string
        source_url?: string
        data_content?: string
    }) {
        try {
            const response = await api.post(`/strategies/${strategyId}/data-sources`, sourceData)

            // Обновляем стратегию в локальном состоянии
            const strategy = strategies.value.find(s => s.id === strategyId)
            if (strategy) {
                strategy.data_sources.push(response.data)
            }

            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка добавления источника данных'
            throw err
        }
    }

    async function uploadDataFile(strategyId: string, file: File) {
        try {
            const formData = new FormData()
            formData.append('file', file)

            const response = await api.post(
                `/strategies/${strategyId}/data-sources/upload-file`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                }
            )

            // Обновляем стратегию
            await fetchStrategies()

            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка загрузки файла'
            throw err
        }
    }

    async function executeStrategy(strategyId: string, executionParams: Record<string, any> = {}) {
        try {
            loading.value = true
            error.value = null

            const response = await api.post(`/strategies/${strategyId}/execute`, {
                execution_params: executionParams
            })

            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка запуска стратегии'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function fetchStrategyExecutions(strategyId?: string) {
        try {
            const params = strategyId ? {strategy_id: strategyId} : {}
            const response = await api.get('/strategies/executions', {params})
            executions.value = response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка загрузки выполнений стратегий'
            throw err
        }
    }

    async function assignStrategiesToProject(assignment: {
        domain_id?: string
        warmup_strategy_id?: string
        position_check_strategy_id?: string
        profile_nurture_strategy_id?: string
    }) {
        try {
            const response = await api.post('/strategies/project-strategies', assignment)
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка назначения стратегий'
            throw err
        }
    }

    async function getProjectStrategies(domainId?: string) {
        try {
            const params = domainId ? {domain_id: domainId} : {}
            const response = await api.get('/strategies/project-strategies', {params})
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка получения назначенных стратегий'
            throw err
        }
    }

    // Profile Nurture specific methods
    async function getAvailableSearchEngines() {
        try {
            const response = await api.get('/strategies/profile-nurture/search-engines')
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка получения поисковых систем'
            throw err
        }
    }

    async function validateProfileNurtureConfig(config: Record<string, any>) {
        try {
            const response = await api.post('/strategies/profile-nurture/validate-config', config)
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка валидации конфигурации'
            throw err
        }
    }

    async function testQuerySource(strategyId: string, sourceData: {
        source_type: string
        source_url?: string
        data_content?: string
    }) {
        try {
            const response = await api.post(`/strategies/${strategyId}/test-query-source`, sourceData)
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка тестирования источника'
            throw err
        }
    }

    async function getNurtureProgress(strategyId: string) {
        try {
            const response = await api.get(`/strategies/${strategyId}/nurture-progress`)
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка получения прогресса нагула'
            throw err
        }
    }

    async function getDefaultConfigs() {
        try {
            const response = await api.get('/strategies/default-configs')
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка получения конфигураций по умолчанию'
            throw err
        }
    }

    // Helper methods for strategy type display
    function getStrategyTypeLabel(type: string): string {
        switch (type) {
            case 'warmup':
                return 'Прогрев'
            case 'position_check':
                return 'Проверка позиций'
            case 'profile_nurture':
                return 'Нагул профиля'
            default:
                return type
        }
    }

    function getStrategyTypeDescription(type: string): string {
        switch (type) {
            case 'warmup':
                return 'Прогрев сайтов перед проверкой позиций'
            case 'position_check':
                return 'Проверка позиций сайтов в поиске'
            case 'profile_nurture':
                return 'Нагул профилей браузера для обхода детекции'
            default:
                return ''
        }
    }

    function getStrategyTypeIcon(type: string): string {
        switch (type) {
            case 'warmup':
                return 'BeakerIcon'
            case 'position_check':
                return 'ChartBarIcon'
            case 'profile_nurture':
                return 'UserIcon'
            default:
                return 'CogIcon'
        }
    }

    function getNurtureTypeLabel(type: string): string {
        switch (type) {
            case 'search_based':
                return 'Через поиск'
            case 'direct_visits':
                return 'Прямые заходы'
            case 'mixed_nurture':
                return 'Смешанный'
            default:
                return type
        }
    }

    // Data import methods for profile nurture
    async function importDataFromUrl(url: string) {
        try {
            const response = await api.post('/strategies/import/url', {url})
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка импорта данных по URL'
            throw err
        }
    }

    async function importDataFromGoogleSheets(url: string) {
        try {
            const response = await api.post('/strategies/import/google-sheets', {url})
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка импорта данных из Google Таблиц'
            throw err
        }
    }

    async function importDataFromGoogleDocs(url: string) {
        try {
            const response = await api.post('/strategies/import/google-docs', {url})
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка импорта данных из Google Документов'
            throw err
        }
    }

    async function validateDataSource(sourceData: {
        source_type: string
        source_url?: string
        data_content?: string
    }) {
        try {
            const response = await api.post('/strategies/validate-data-source', sourceData)
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка валидации источника данных'
            throw err
        }
    }

    // File processing methods
    async function processTextFile(file: File) {
        try {
            const content = await readFileAsText(file)
            return {
                type: 'manual_input',
                data_content: content,
                items_count: content.split('\n').filter(line => line.trim()).length
            }
        } catch (err: any) {
            error.value = 'Ошибка чтения текстового файла'
            throw err
        }
    }

    async function processCsvFile(file: File) {
        try {
            const content = await readFileAsText(file)
            // Простая обработка CSV - берем первую колонку
            const lines = content.split('\n')
            const processedLines = lines.map(line => {
                const cells = line.split(',')
                return cells[0]?.trim() || ''
            }).filter(line => line)

            return {
                type: 'manual_input',
                data_content: processedLines.join('\n'),
                items_count: processedLines.length
            }
        } catch (err: any) {
            error.value = 'Ошибка чтения CSV файла'
            throw err
        }
    }

    function readFileAsText(file: File): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = (e) => {
                const content = e.target?.result as string
                resolve(content)
            }
            reader.onerror = reject
            reader.readAsText(file)
        })
    }

    function getDataSourceStats(source: any) {
        if (!source.data_content) return {count: 0, preview: []}

        const lines = source.data_content.split('\n').filter(line => line.trim())
        return {
            count: lines.length,
            preview: lines.slice(0, 5),
            isEmpty: lines.length === 0,
            isMinimal: lines.length < 10,
            isGood: lines.length >= 10
        }
    }

    function getEnhancedProfileNurtureConfig() {
        return {
            nurture_type: 'search_based',
            target_cookies: {
                min: 50,
                max: 100
            },
            session_config: {
                timeout_per_site: 15,
                min_timeout: 10,
                max_timeout: 30
            },
            search_engines: ['yandex.ru'],
            queries_source: {
                type: 'manual_input',
                data_content: '',
                source_url: '',
                refresh_on_each_cycle: false
            },
            behavior: {
                return_to_search: true,
                close_browser_after_cycle: false,
                emulate_human_actions: true,
                scroll_pages: true,
                random_clicks: true
            },
            proportions: {
                search_visits: 70,
                direct_visits: 30
            },
            direct_sites_source: {
                type: 'manual_input',
                data_content: '',
                source_url: '',
                refresh_on_each_cycle: false
            }
        }
    }

    function cleanProfileNurtureConfig(config) {
        const cleaned = {...config}

        // Удаляем поля, которые не нужны для определенных типов
        if (cleaned.nurture_type === 'search_based') {
            delete cleaned.direct_sites_source
            delete cleaned.proportions
        } else if (cleaned.nurture_type === 'direct_visits') {
            delete cleaned.search_engines
            delete cleaned.proportions
            // Очищаем queries_source, но оставляем пустую структуру
            cleaned.queries_source = {
                type: 'manual_input',
                data_content: '',
                source_url: '',
                refresh_on_each_cycle: false
            }
        }

        return cleaned
    }

    function validateQueriesSource(source) {
        const errors = []

        if (!source) {
            errors.push('Источник запросов обязателен')
            return errors
        }

        if (source.type === 'manual_input' && !source.data_content?.trim()) {
            errors.push('Поисковые запросы не могут быть пустыми')
        }

        if (['url_import', 'google_sheets', 'google_docs'].includes(source.type) && !source.source_url?.trim()) {
            errors.push('URL источника запросов обязателен')
        }

        return errors
    }

    function validateDirectSitesSource(source) {
        const errors = []

        if (!source) {
            errors.push('Источник сайтов обязателен')
            return errors
        }

        if (source.type === 'manual_input' && !source.data_content?.trim()) {
            errors.push('Список сайтов не может быть пустым')
        }

        if (['url_import', 'google_sheets', 'google_docs'].includes(source.type) && !source.source_url?.trim()) {
            errors.push('URL источника сайтов обязателен')
        }

        return errors
    }

    async function createTemporaryStrategy(strategyData) {
        try {
            const response = await api.post('/strategies/temporary', strategyData)
            return response.data
        } catch (err) {
            error.value = err.response?.data?.detail || 'Ошибка создания временной стратегии'
            throw err
        }
    }

    return {
        // State
        strategies,
        templates,
        executions,
        loading,
        error,

        // Computed
        warmupStrategies,
        positionCheckStrategies,
        profileNurtureStrategies,
        warmupTemplates,
        positionCheckTemplates,
        profileNurtureTemplates,

        // Methods
        fetchStrategyTemplates,
        fetchStrategies,
        createStrategy,
        updateStrategy,
        deleteStrategy,
        addDataSource,
        uploadDataFile,
        executeStrategy,
        fetchStrategyExecutions,
        assignStrategiesToProject,
        getProjectStrategies,

        // Profile Nurture specific
        getAvailableSearchEngines,
        validateProfileNurtureConfig,
        testQuerySource,
        getNurtureProgress,
        getDefaultConfigs,

        // Default configs
        getDefaultWarmupConfig,
        getDefaultPositionCheckConfig,
        getDefaultProfileNurtureConfig,

        // Helper methods
        getStrategyTypeLabel,
        getStrategyTypeDescription,
        getStrategyTypeIcon,
        getNurtureTypeLabel,

        importDataFromUrl,
        importDataFromGoogleSheets,
        importDataFromGoogleDocs,
        validateDataSource,
        createTemporaryStrategy,
        processTextFile,
        processCsvFile,
        readFileAsText,
        getEnhancedProfileNurtureConfig,
        validateQueriesSource,
        validateDirectSitesSource,
        getDataSourceStats,

        cleanProfileNurtureConfig
    }
})

