<!-- frontend/src/components/admin/TaskDebugPanel.vue -->
<template>
    <div class="task-debug-panel">
        <!-- Header -->
        <div class="bg-white shadow rounded-lg mb-6">
            <div class="px-4 py-5 sm:p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg leading-6 font-medium text-gray-900">
                            Система дебага задач VNC
                        </h3>
                        <p class="mt-1 text-sm text-gray-500">
                            Управление debug сессиями для мониторинга браузеров в реальном времени
                        </p>
                    </div>
                    <div class="flex space-x-3">
                        <button
                            @click="refreshSessions"
                            :disabled="loading"
                            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                        >
                            <svg v-if="loading"
                                 class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline"
                                 fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10"
                                        stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor"
                                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Обновить
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Active Debug Sessions -->
        <div class="bg-white shadow rounded-lg mb-6" v-if="activeSessions.length > 0">
            <div class="px-4 py-5 sm:p-6">
                <h4 class="text-md font-medium text-gray-900 mb-4">Активные VNC сессии
                    ({{ activeSessions.length }})</h4>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div
                        v-for="session in activeSessions"
                        :key="session.task_id"
                        class="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                    >
                        <div class="flex items-center justify-between mb-3">
                            <div class="flex items-center">
                                <div class="w-3 h-3 bg-green-400 rounded-full mr-2"></div>
                                <span class="text-sm font-medium text-gray-900">Task {{
                                        session.task_id.slice(0, 8)
                                    }}</span>
                            </div>
                            <span
                                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  session.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                ]"
                            >
                {{ session.status }}
              </span>
                        </div>

                        <div class="space-y-2 text-sm text-gray-600">
                            <div class="flex justify-between">
                                <span>VNC порт:</span>
                                <span class="font-mono">{{ session.vnc_port }}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Разрешение:</span>
                                <span class="font-mono">{{ session.resolution }}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Устройство:</span>
                                <span class="capitalize">{{ session.device_type }}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Создано:</span>
                                <span>{{ formatTime(session.created_at) }}</span>
                            </div>
                        </div>

                        <div class="mt-4 flex space-x-2">
                            <button
                                @click="showVncInstructions(session.task_id)"
                                class="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs font-medium"
                            >
                                Подключиться
                            </button>
                            <button
                                @click="viewScreenshot(session.task_id)"
                                class="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-xs font-medium"
                            >
                                Скриншот
                            </button>
                            <button
                                @click="stopDebugSession(session.task_id)"
                                class="flex-1 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs font-medium"
                            >
                                Остановить
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tasks List -->
        <div class="bg-white shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
                <div class="flex items-center justify-between mb-4">
                    <h4 class="text-md font-medium text-gray-900">Задачи для дебага</h4>
                    <div class="flex space-x-2">
                        <select v-model="statusFilter" @change="loadTasks"
                                class="text-sm border-gray-300 rounded-md">
                            <option value="">Все статусы</option>
                            <option value="pending">Ожидание</option>
                            <option value="running">Выполняется</option>
                            <option value="failed">Ошибка</option>
                            <option value="completed">Завершено</option>
                        </select>
                        <select v-model="deviceTypeFilter"
                                class="text-sm border-gray-300 rounded-md">
                            <option value="desktop">Desktop</option>
                            <option value="mobile">Mobile</option>
                            <option value="tablet">Tablet</option>
                        </select>
                    </div>
                </div>

                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Task ID
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Тип
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Статус
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Параметры
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Debug
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Действия
                            </th>
                        </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-for="task in tasks" :key="task.task_id" class="hover:bg-gray-50">
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                                {{ task.task_id.slice(0, 8) }}...
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {{ getTaskTypeText(task.task_type) }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                  <span
                      :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      getTaskStatusClass(task.status)
                    ]"
                  >
                    {{ getTaskStatusText(task.status) }}
                  </span>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-600">
                                <div v-if="task.parameters?.keyword" class="mb-1">
                                    <span class="font-medium">Запрос:</span>
                                    {{ task.parameters.keyword }}
                                </div>
                                <div v-if="task.parameters?.device_type" class="mb-1">
                                    <span class="font-medium">Устройство:</span>
                                    {{ task.parameters.device_type }}
                                </div>
                                <div v-if="task.parameters?.region_code" class="mb-1">
                                    <span class="font-medium">Регион:</span>
                                    {{ task.parameters.region_code }}
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                  <span
                      v-if="task.parameters?.debug_enabled"
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                  >
                    Debug активен
                  </span>
                                <span
                                    v-else
                                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                                >
                    Обычный режим
                  </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                <button
                                    v-if="!task.parameters?.debug_enabled && ['pending', 'running', 'failed'].includes(task.status)"
                                    @click="startDebugSession(task.task_id)"
                                    :disabled="debugActionLoading[task.task_id]"
                                    class="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                                >
                                    Запустить Debug
                                </button>

                                <button
                                    v-if="task.parameters?.debug_enabled"
                                    @click="stopDebugSession(task.task_id)"
                                    :disabled="debugActionLoading[task.task_id]"
                                    class="text-red-600 hover:text-red-900 disabled:opacity-50"
                                >
                                    Остановить Debug
                                </button>

                                <button
                                    v-if="task.parameters?.debug_enabled"
                                    @click="showVncInstructions(task.task_id)"
                                    class="text-green-600 hover:text-green-900"
                                >
                                    VNC инфо
                                </button>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Pagination -->
                <div class="mt-4 flex items-center justify-between">
                    <div class="text-sm text-gray-700">
                        Показано {{ tasks.length }} из {{ totalTasks }}
                    </div>
                    <div class="flex space-x-2">
                        <button
                            @click="loadMoreTasks"
                            v-if="tasks.length < totalTasks"
                            :disabled="loading"
                            class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                        >
                            Загрузить еще
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- VNC Instructions Modal -->
        <VncInstructionsModal
            :isOpen="showVncModal"
            :taskId="selectedTaskId"
            @close="showVncModal = false"
        />

        <!-- Screenshot Modal -->
        <ScreenshotModal
            :isOpen="showScreenshotModal"
            :taskId="selectedTaskId"
            @close="showScreenshotModal = false"
        />
    </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import VncInstructionsModal from './VncInstructionsModal.vue'
import ScreenshotModal from './ScreenshotModal.vue'

// Reactive data
const loading = ref(false)
const tasks = ref([])
const activeSessions = ref([])
const statusFilter = ref('')
const deviceTypeFilter = ref('desktop')
const debugActionLoading = ref({})
const totalTasks = ref(0)
const currentPage = ref(0)
const pageSize = ref(20)

// Modals
const showVncModal = ref(false)
const showScreenshotModal = ref(false)
const selectedTaskId = ref('')

// Mock API для тестирования (замените на реальные API вызовы)
const api = {
    get: async (url) => {
        console.log('GET:', url)

        if (url.includes('/admin/debug/sessions')) {
            return {data: []}
        }

        if (url.includes('/admin/tasks')) {
            return {
                data: {
                    tasks: [
                        {
                            task_id: 'test-task-1',
                            task_type: 'parse_serp',
                            status: 'pending',
                            parameters: {
                                keyword: 'test query',
                                device_type: 'desktop',
                                region_code: '213',
                                debug_enabled: false
                            }
                        }
                    ],
                    total: 1
                }
            }
        }

        return {data: {}}
    },

    post: async (url, data) => {
        console.log('POST:', url, data)
        return {
            data: {
                success: true,
                message: 'Success'
            }
        }
    }
}

// Methods
const loadTasks = async (reset = true) => {
    try {
        loading.value = true

        if (reset) {
            currentPage.value = 0
            tasks.value = []
        }

        const response = await api.get('/admin/tasks', {
            params: {
                limit: pageSize.value,
                offset: currentPage.value * pageSize.value,
                status: statusFilter.value || undefined
            }
        })

        if (reset) {
            tasks.value = response.data.tasks
        } else {
            tasks.value.push(...response.data.tasks)
        }

        totalTasks.value = response.data.total
        currentPage.value++

    } catch (error) {
        console.error('Failed to load tasks:', error)
        showToast('Ошибка загрузки задач', 'error')
    } finally {
        loading.value = false
    }
}

const loadMoreTasks = () => {
    loadTasks(false)
}

const refreshSessions = async () => {
    try {
        const response = await api.get('/admin/debug/sessions')
        activeSessions.value = response.data
    } catch (error) {
        console.error('Failed to load debug sessions:', error)
        showToast('Ошибка загрузки debug сессий', 'error')
    }
}

const startDebugSession = async (taskId) => {
    try {
        debugActionLoading.value[taskId] = true

        const response = await api.post(`/admin/debug/start/${taskId}`, {
            device_type: deviceTypeFilter.value
        })

        if (response.data.success) {
            showToast('Debug сессия запущена успешно', 'success')
            await loadTasks()
            await refreshSessions()
        }
    } catch (error) {
        console.error('Failed to start debug session:', error)
        showToast('Ошибка запуска debug сессии', 'error')
    } finally {
        debugActionLoading.value[taskId] = false
    }
}

const stopDebugSession = async (taskId) => {
    try {
        debugActionLoading.value[taskId] = true

        const response = await api.post(`/admin/debug/stop/${taskId}`)

        if (response.data.success) {
            showToast('Debug сессия остановлена', 'success')
            await loadTasks()
            await refreshSessions()
        }
    } catch (error) {
        console.error('Failed to stop debug session:', error)
        showToast('Ошибка остановки debug сессии', 'error')
    } finally {
        debugActionLoading.value[taskId] = false
    }
}

const showVncInstructions = (taskId) => {
    selectedTaskId.value = taskId
    showVncModal.value = true
}

const viewScreenshot = (taskId) => {
    selectedTaskId.value = taskId
    showScreenshotModal.value = true
}

// Utility methods
const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    })
}

const getTaskTypeText = (type) => {
    const types = {
        'warmup_profile': 'Прогрев профиля',
        'parse_serp': 'Парсинг SERP',
        'check_positions': 'Проверка позиций',
        'health_check': 'Проверка здоровья',
        'maintain_profiles': 'Обслуживание профилей'
    }
    return types[type] || type
}

const getTaskStatusText = (status) => {
    const statuses = {
        'pending': 'Ожидание',
        'running': 'Выполняется',
        'completed': 'Завершено',
        'failed': 'Ошибка',
        'retrying': 'Повтор'
    }
    return statuses[status] || status
}

const getTaskStatusClass = (status) => {
    const classes = {
        'pending': 'bg-yellow-100 text-yellow-800',
        'running': 'bg-blue-100 text-blue-800',
        'completed': 'bg-green-100 text-green-800',
        'failed': 'bg-red-100 text-red-800',
        'retrying': 'bg-orange-100 text-orange-800'
    }
    return classes[status] || 'bg-gray-100 text-gray-800'
}

const showToast = (message, type) => {
    console.log(`${type.toUpperCase()}: ${message}`)
    // Здесь можно интегрировать с системой уведомлений
}

// Lifecycle
onMounted(async () => {
    await loadTasks()
    await refreshSessions()

    // Обновляем сессии каждые 30 секунд
    setInterval(refreshSessions, 30000)
})
</script>

<style scoped>
.task-debug-panel {
    @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8;
}
</style>
