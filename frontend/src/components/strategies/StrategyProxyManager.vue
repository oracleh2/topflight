<!-- frontend/src/components/strategies/StrategyProxyManager.vue -->
<template>
    <div class="bg-white shadow-sm rounded-lg p-6 mt-6">
        <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-medium text-gray-900">
                <GlobeAltIcon class="h-5 w-5 inline mr-2"/>
                Управление прокси
            </h3>
            <div class="flex items-center space-x-4">
                <span
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {{ stats.total_proxies }} прокси
                </span>
                <button
                    @click="showAddProxyModal = true"
                    class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                    <PlusIcon class="h-4 w-4 mr-1"/>
                    Добавить прокси
                </button>
            </div>
        </div>

        <!-- Статистика прокси -->
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-4 mb-6">
            <div class="bg-gray-50 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <ChartBarIcon class="h-5 w-5 text-gray-400"/>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">Всего прокси</p>
                        <p class="text-lg font-semibold text-gray-900">{{ stats.total_proxies }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-green-50 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <CheckCircleIcon class="h-5 w-5 text-green-400"/>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">Активных</p>
                        <p class="text-lg font-semibold text-green-600">{{
                                stats.active_proxies
                            }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-red-50 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <XCircleIcon class="h-5 w-5 text-red-400"/>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">Неактивных</p>
                        <p class="text-lg font-semibold text-red-600">{{ stats.failed_proxies }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-blue-50 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <CpuChipIcon class="h-5 w-5 text-blue-400"/>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">Успешность</p>
                        <p class="text-lg font-semibold text-blue-600">
                            {{ stats.success_rate ? Math.round(stats.success_rate) + '%' : 'Н/Д' }}
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Настройки прокси -->
        <div class="border rounded-lg p-4 mb-6">
            <h4 class="text-md font-medium text-gray-900 mb-4">Настройки прокси</h4>
            <div class="space-y-4">
                <div class="flex items-center justify-between">
                    <div>
                        <label class="text-sm font-medium text-gray-700">Использовать прокси</label>
                        <p class="text-sm text-gray-500">Включить использование прокси для этой
                            стратегии</p>
                    </div>
                    <input
                        v-model="proxySettings.use_proxy"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        @change="updateProxySettings"
                    >
                </div>

                <div class="flex items-center justify-between">
                    <div>
                        <label class="text-sm font-medium text-gray-700">Ротация прокси</label>
                        <p class="text-sm text-gray-500">Автоматически менять прокси после
                            определенного количества запросов</p>
                    </div>
                    <input
                        v-model="proxySettings.proxy_rotation"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        @change="updateProxySettings"
                    >
                </div>

                <div v-if="proxySettings.proxy_rotation" class="flex items-center justify-between">
                    <div>
                        <label class="text-sm font-medium text-gray-700">Интервал ротации</label>
                        <p class="text-sm text-gray-500">Количество запросов до смены прокси</p>
                    </div>
                    <input
                        v-model.number="proxySettings.proxy_rotation_interval"
                        type="number"
                        min="1"
                        max="100"
                        class="w-20 px-2 py-1 border border-gray-300 rounded-md text-sm"
                        @blur="updateProxySettings"
                    >
                </div>

                <div class="flex items-center justify-between">
                    <div>
                        <label class="text-sm font-medium text-gray-700">Запасные прокси</label>
                        <p class="text-sm text-gray-500">Использовать другие прокси при сбое
                            основной</p>
                    </div>
                    <input
                        v-model="proxySettings.fallback_on_error"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        @change="updateProxySettings"
                    >
                </div>
            </div>
        </div>

        <!-- Список прокси -->
        <div class="border rounded-lg">
            <div class="px-4 py-3 border-b border-gray-200">
                <h4 class="text-md font-medium text-gray-900">Прокси</h4>
            </div>
            <div class="divide-y divide-gray-200">
                <div
                    v-for="proxy in proxies"
                    :key="proxy.id"
                    class="p-4 hover:bg-gray-50"
                >
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <div
                                :class="[
                                    'h-2 w-2 rounded-full',
                                    proxy.status === 'active' ? 'bg-green-500' : 'bg-red-500'
                                ]"
                            ></div>
                            <div>
                                <p class="text-sm font-medium text-gray-900">
                                    {{ proxy.host }}:{{ proxy.port }}
                                </p>
                                <p class="text-xs text-gray-500">
                                    {{ proxy.protocol.toUpperCase() }} •
                                    Использований: {{ proxy.total_uses }} •
                                    Успешность: {{ proxy.success_rate }}%
                                </p>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span :class="[
                                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                                proxy.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            ]">
                                {{ proxy.status === 'active' ? 'Активна' : 'Неактивна' }}
                            </span>
                            <button
                                @click="testProxy(proxy)"
                                class="text-blue-600 hover:text-blue-900 text-sm font-medium"
                            >
                                Тест
                            </button>
                        </div>
                    </div>
                </div>
                <div v-if="proxies.length === 0" class="p-4 text-center text-gray-500">
                    Прокси не добавлены
                </div>
            </div>
        </div>

        <!-- Источники прокси -->
        <div v-if="proxySources.length > 0" class="border rounded-lg mt-6">
            <div class="px-4 py-3 border-b border-gray-200">
                <h4 class="text-md font-medium text-gray-900">Источники прокси</h4>
            </div>
            <div class="divide-y divide-gray-200">
                <div
                    v-for="source in proxySources"
                    :key="source.id"
                    class="p-4 hover:bg-gray-50"
                >
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-gray-900">
                                {{ getSourceTypeLabel(source.source_type) }}
                            </p>
                            <p class="text-xs text-gray-500">
                                {{ formatDate(source.created_at) }} •
                                {{ source.proxy_count }} прокси
                            </p>
                        </div>
                        <button
                            @click="deleteProxySource(source.id)"
                            class="text-red-600 hover:text-red-900 text-sm font-medium"
                        >
                            Удалить
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Модальное окно добавления прокси -->
    <AddStrategyProxyModal
        v-if="showAddProxyModal"
        :strategy-id="strategyId"
        @close="showAddProxyModal = false"
        @success="handleProxyAdded"
    />
</template>

<script setup lang="ts">
import {onMounted, ref, watch} from 'vue'
import {
    ChartBarIcon,
    CheckCircleIcon,
    CpuChipIcon,
    GlobeAltIcon,
    PlusIcon,
    XCircleIcon
} from '@heroicons/vue/24/outline'
import AddStrategyProxyModal from './AddStrategyProxyModal.vue'
import {useStrategiesStore} from '@/stores/strategies'

// Props
interface Props {
    strategyId: string
}

const props = defineProps<Props>()

// Store
const strategiesStore = useStrategiesStore()

// Reactive data
const loading = ref(false)
const proxies = ref([])
const proxySources = ref([])
const stats = ref({
    total_proxies: 0,
    active_proxies: 0,
    failed_proxies: 0,
    success_rate: null
})
const proxySettings = ref({
    use_proxy: true,
    proxy_rotation: true,
    proxy_rotation_interval: 10,
    fallback_on_error: true,
    max_retries: 3,
    retry_delay: 5
})
const showAddProxyModal = ref(false)

// Methods
const loadProxies = async () => {
    loading.value = true
    try {
        proxies.value = await strategiesStore.getStrategyProxies(props.strategyId)
    } catch (error) {
        console.error('Error loading proxies:', error)
    } finally {
        loading.value = false
    }
}

const loadProxyStats = async () => {
    try {
        stats.value = await strategiesStore.getStrategyProxyStats(props.strategyId)
    } catch (error) {
        console.error('Error loading proxy stats:', error)
    }
}

const loadProxySources = async () => {
    try {
        proxySources.value = await strategiesStore.getStrategyProxySources(props.strategyId)
    } catch (error) {
        console.error('Error loading proxy sources:', error)
    }
}

const updateProxySettings = async () => {
    try {
        await strategiesStore.updateStrategyProxySettings(props.strategyId, proxySettings.value)
    } catch (error) {
        console.error('Error updating proxy settings:', error)
    }
}

const testProxy = async (proxy: any) => {
    try {
        await strategiesStore.testStrategyProxy(props.strategyId, proxy.id)
        console.log('Proxy test completed')
    } catch (error) {
        console.error('Error testing proxy:', error)
    }
}


const deleteProxySource = async (sourceId: string) => {
    if (!confirm('Удалить источник прокси?')) return

    try {
        await strategiesStore.deleteStrategyProxySource(props.strategyId, sourceId)
        await loadProxySources()
        await loadProxies()
        await loadProxyStats()
    } catch (error) {
        console.error('Error deleting proxy source:', error)
    }
}

const handleProxyAdded = () => {
    showAddProxyModal.value = false
    loadProxies()
    loadProxyStats()
    loadProxySources()
}

const getSourceTypeLabel = (type: string) => {
    const labels = {
        'manual_list': 'Ручной ввод',
        'file_upload': 'Файл',
        'url_import': 'URL импорт',
        'google_sheets': 'Google Таблицы',
        'google_docs': 'Google Документы'
    }
    return labels[type] || type
}

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU')
}

// Lifecycle
onMounted(() => {
    loadProxies()
    loadProxyStats()
    loadProxySources()
})

// Watchers
watch(() => props.strategyId, () => {
    loadProxies()
    loadProxyStats()
    loadProxySources()
})
</script>
