<!-- frontend/src/components/proxy/ProxyManager.vue -->
<template>
    <div class="space-y-6">
        <!-- Заголовок -->
        <div class="flex justify-between items-center">
            <h3 class="text-lg font-medium text-gray-900">Управление прокси</h3>
            <button
                @click="showImportModal = true"
                class="btn-primary"
            >
                <PlusIcon class="h-4 w-4 mr-2"/>
                Добавить прокси
            </button>
        </div>

        <!-- Табы для типов прокси -->
        <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8">
                <button
                    v-for="tab in tabs"
                    :key="tab.key"
                    @click="activeTab = tab.key"
                    :class="[
            activeTab === tab.key
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
            'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
          ]"
                >
                    {{ tab.name }}
                    <span
                        v-if="tab.count > 0"
                        :class="[
              activeTab === tab.key
                ? 'bg-primary-100 text-primary-600'
                : 'bg-gray-100 text-gray-900',
              'ml-2 py-0.5 px-2.5 rounded-full text-xs font-medium'
            ]"
                    >
            {{ tab.count }}
          </span>
                </button>
            </nav>
        </div>

        <!-- Список прокси -->
        <div class="bg-white shadow overflow-hidden sm:rounded-md">
            <div v-if="loading" class="p-6 text-center">
                <div
                    class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
                <p class="mt-2 text-sm text-gray-500">Загрузка прокси...</p>
            </div>

            <div v-else-if="currentProxies.length === 0" class="p-6 text-center">
                <ServerIcon class="mx-auto h-12 w-12 text-gray-300"/>
                <h3 class="mt-2 text-sm font-medium text-gray-900">
                    Прокси для {{ activeTab === 'warmup' ? 'нагула' : 'замеров' }} не добавлены
                </h3>
                <p class="mt-1 text-sm text-gray-500">
                    Добавьте прокси для улучшения качества парсинга
                </p>
                <button
                    @click="showImportModal = true"
                    class="mt-4 btn-primary"
                >
                    Добавить прокси
                </button>
            </div>

            <ul v-else class="divide-y divide-gray-200">
                <li
                    v-for="proxy in currentProxies"
                    :key="proxy.id"
                    class="p-4 hover:bg-gray-50"
                >
                    <div class="flex items-center justify-between">
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div
                                        :class="[
                      proxy.status === 'active' ? 'bg-green-100 text-green-800' :
                      proxy.status === 'inactive' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800',
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'
                    ]"
                                    >
                                        {{ getStatusText(proxy.status) }}
                                    </div>
                                </div>
                                <div class="ml-4 flex-1 min-w-0">
                                    <p class="text-sm font-medium text-gray-900">
                                        {{ proxy.host }}:{{ proxy.port }}
                                    </p>
                                    <div class="flex items-center space-x-4 mt-1">
                                        <p class="text-sm text-gray-500">
                                            {{ proxy.protocol.toUpperCase() }}
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Успешность: {{ proxy.success_rate }}%
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Использований: {{ proxy.total_uses }}
                                        </p>
                                        <p v-if="proxy.response_time" class="text-sm text-gray-500">
                                            {{ proxy.response_time }}ms
                                        </p>
                                        <p v-if="proxy.country" class="text-sm text-gray-500">
                                            {{ proxy.country }}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <button
                                @click="testProxy(proxy.id)"
                                :disabled="testingProxies.includes(proxy.id)"
                                class="btn-secondary text-xs py-1 px-2"
                            >
                <span v-if="testingProxies.includes(proxy.id)">
                  Тестируется...
                </span>
                                <span v-else>Тест</span>
                            </button>
                            <button
                                @click="deleteProxy(proxy.id)"
                                :disabled="deletingProxies.includes(proxy.id)"
                                class="btn-danger text-xs py-1 px-2"
                            >
                                <TrashIcon class="h-3 w-3"/>
                            </button>
                        </div>
                    </div>
                </li>
            </ul>
        </div>

        <!-- Модальное окно импорта -->
        <ProxyImportModal
            :is-open="showImportModal"
            :domain-id="domainId"
            @close="showImportModal = false"
            @success="handleImportSuccess"
        />
    </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, watch} from 'vue'
import {PlusIcon, ServerIcon, TrashIcon} from '@heroicons/vue/24/outline'
import {api} from '@/api'
import ProxyImportModal from './ProxyImportModal.vue'

interface Props {
    domainId: string
}

const props = defineProps<Props>()

interface Proxy {
    id: string
    host: string
    port: number
    protocol: string
    status: string
    success_rate: number
    total_uses: number
    response_time?: number
    country?: string
    created_at: string
}

// State
const loading = ref(false)
const showImportModal = ref(false)
const activeTab = ref<'warmup' | 'parsing'>('warmup')
const testingProxies = ref<string[]>([])
const deletingProxies = ref<string[]>([])

const warmupProxies = ref<Proxy[]>([])
const parsingProxies = ref<Proxy[]>([])

// Computed
const tabs = computed(() => [
    {
        key: 'warmup',
        name: 'Прокси для нагула',
        count: warmupProxies.value?.length || 0
    },
    {
        key: 'parsing',
        name: 'Прокси для замеров',
        count: parsingProxies.value?.length || 0
    }
])

const currentProxies = computed(() => {
    const proxies = activeTab.value === 'warmup' ? warmupProxies.value : parsingProxies.value
    return proxies || []
})

// Methods
const getStatusText = (status: string) => {
    switch (status) {
        case 'active':
            return 'Активна'
        case 'inactive':
            return 'Неактивна'
        case 'checking':
            return 'Проверяется'
        case 'banned':
            return 'Заблокирована'
        default:
            return status
    }
}

const loadProxies = async () => {
    loading.value = true
    try {
        const response = await api.get(`/proxies/domain/${props.domainId}`)
        if (response.data.success) {
            const proxies = response.data.data || []

            // Разделяем прокси по типам
            warmupProxies.value = proxies.filter(p => p.proxy_type === 'warmup')
            parsingProxies.value = proxies.filter(p => p.proxy_type === 'parsing')
        }
    } catch (error) {
        console.error('Ошибка загрузки прокси:', error)
        // В случае ошибки инициализируем пустыми массивами
        warmupProxies.value = []
        parsingProxies.value = []
    } finally {
        loading.value = false
    }
}

const testProxy = async (proxyId: string) => {
    testingProxies.value.push(proxyId)
    try {
        const response = await api.get(`/proxies/test/${proxyId}`)
        if (response.data.success) {
            // Можно показать уведомление о результате теста
            console.log('Тест прокси завершен')
        }
    } catch (error) {
        console.error('Ошибка тестирования прокси:', error)
    } finally {
        testingProxies.value = testingProxies.value.filter(id => id !== proxyId)
    }
}

const deleteProxy = async (proxyId: string) => {
    if (!confirm('Вы уверены, что хотите удалить эту прокси?')) {
        return
    }

    deletingProxies.value.push(proxyId)
    try {
        const response = await api.delete(`/proxies/${proxyId}`)
        if (response.data.success) {
            // Удаляем из локального состояния
            warmupProxies.value = warmupProxies.value.filter(p => p.id !== proxyId)
            parsingProxies.value = parsingProxies.value.filter(p => p.id !== proxyId)
        }
    } catch (error) {
        console.error('Ошибка удаления прокси:', error)
    } finally {
        deletingProxies.value = deletingProxies.value.filter(id => id !== proxyId)
    }
}

const handleImportSuccess = () => {
    showImportModal.value = false
    loadProxies()
}

// Lifecycle
onMounted(() => {
    loadProxies()
})

watch(() => props.domainId, () => {
    if (props.domainId) {
        loadProxies()
    }
})
</script>
