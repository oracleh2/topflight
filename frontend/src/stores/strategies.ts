// frontend/src/stores/strategies.ts
import {defineStore} from 'pinia'
import {ref, computed} from 'vue'
import {api} from '@/api'

export interface StrategyTemplate {
    id: string
    name: string
    description?: string
    strategy_type: 'warmup' | 'position_check'
    config: Record<string, any>
    is_system: boolean
    created_at: string
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

export interface UserStrategy {
    id: string
    user_id: string
    template_id?: string
    name: string
    strategy_type: 'warmup' | 'position_check'
    config: Record<string, any>
    created_at: string
    updated_at: string
    is_active: boolean
    data_sources: DataSource[]
}

export interface StrategyExecution {
    id: string
    strategy_id: string
    task_id?: string
    execution_type: 'warmup' | 'position_check'
    profile_id?: string
    parameters?: Record<string, any>
    result?: Record<string, any>
    status: 'pending' | 'running' | 'completed' | 'failed'
    started_at?: string
    completed_at?: string
    error_message?: string
}

export const useStrategiesStore = defineStore('strategies', () => {
    // State
    const templates = ref<StrategyTemplate[]>([])
    const strategies = ref<UserStrategy[]>([])
    const executions = ref<StrategyExecution[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)

    // Computed
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

    // Actions
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
        strategy_type: 'warmup' | 'position_check'
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

            const index = strategies.value.findIndex(s => s.id === strategyId)
            if (index !== -1) {
                strategies.value[index] = response.data
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

            strategies.value = strategies.value.filter(s => s.id !== strategyId)
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка удаления стратегии'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function duplicateStrategy(strategyId: string, newName: string) {
        try {
            const strategy = strategies.value.find(s => s.id === strategyId)
            if (!strategy) {
                throw new Error('Стратегия не найдена')
            }

            const newStrategy = await createStrategy({
                name: newName,
                strategy_type: strategy.strategy_type,
                config: {...strategy.config}
            })

            // Копируем источники данных
            for (const dataSource of strategy.data_sources) {
                await addDataSource(newStrategy.id, {
                    source_type: dataSource.source_type,
                    source_url: dataSource.source_url,
                    data_content: dataSource.data_content
                })
            }

            await fetchStrategies() // Перезагружаем для получения актуальных данных
            return newStrategy
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка дублирования стратегии'
            throw err
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

    // Strategy configuration helpers
    function getDefaultWarmupConfig() {
        return {
            type: 'mixed',
            proportions: {
                direct_visits: 5,
                search_visits: 1
            },
            search_config: {
                yandex_domains: ['yandex.ru'],
                keywords_per_session: {min: 1, max: 3},
                click_probability: 0.7,
                random_result_click: true
            },
            direct_config: {
                sites_per_session: {min: 3, max: 7},
                time_per_site: {min: 10, max: 45},
                scroll_probability: 0.8,
                click_probability: 0.3
            },
            general: {
                delay_between_actions: {min: 2, max: 8},
                user_agent_rotation: true,
                cookie_retention: true
            }
        }
    }

    function getDefaultPositionCheckConfig() {
        return {
            check_frequency: 'daily',
            search_config: {
                pages_to_check: 10,
                yandex_domain: 'yandex.ru',
                device_types: ['desktop'],
                regions: ['213']
            },
            behavior: {
                scroll_serp: true,
                click_competitors: 0.1,
                time_on_serp: {min: 5, max: 15}
            }
        }
    }

    return {
        // State
        templates,
        strategies,
        executions,
        loading,
        error,

        // Computed
        warmupStrategies,
        positionCheckStrategies,
        warmupTemplates,
        positionCheckTemplates,

        // Actions
        fetchStrategyTemplates,
        fetchStrategies,
        createStrategy,
        updateStrategy,
        deleteStrategy,
        duplicateStrategy,
        addDataSource,
        uploadDataFile,
        executeStrategy,
        fetchStrategyExecutions,
        assignStrategiesToProject,
        getProjectStrategies,

        // Helpers
        getDefaultWarmupConfig,
        getDefaultPositionCheckConfig
    }
})
