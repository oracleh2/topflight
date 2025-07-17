<!-- frontend/src/components/strategies/ProfileNurtureTasksMonitor.vue -->
<template>
    <div class="bg-white shadow rounded-lg">

        <div class="px-4 py-2 bg-gray-100 text-xs text-gray-600">
            Strategy ID: {{ strategyId }}
        </div>

        <!-- Заголовок -->
        <div class="px-4 py-5 sm:p-6">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-medium text-gray-900">
                    Задачи нагула профилей
                </h3>
                <div class="flex space-x-2">
                    <button
                        @click="refreshTasks"
                        :disabled="loading"
                        class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                    >
                        <ArrowPathIcon
                            :class="['h-4 w-4 mr-1', { 'animate-spin': loading }]"/>
                        Обновить
                    </button>
                    <button
                        @click="showCreateTaskModal = true"
                        class="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                        <PlusIcon class="h-4 w-4 mr-1"/>
                        Создать задачи
                    </button>
                </div>
            </div>

            <!-- Статистика -->
            <div v-if="stats" class="grid grid-cols-2 gap-4 sm:grid-cols-5 mb-6">
                <div class="bg-gray-50 rounded-lg p-3">
                    <div class="text-sm font-medium text-gray-500">Всего</div>
                    <div class="mt-1 text-2xl font-semibold text-gray-900">
                        {{ stats.total }}
                    </div>
                </div>
                <div class="bg-yellow-50 rounded-lg p-3">
                    <div class="text-sm font-medium text-yellow-600">Ожидают</div>
                    <div class="mt-1 text-2xl font-semibold text-yellow-700">
                        {{ stats.pending }}
                    </div>
                </div>
                <div class="bg-blue-50 rounded-lg p-3">
                    <div class="text-sm font-medium text-blue-600">Выполняются</div>
                    <div class="mt-1 text-2xl font-semibold text-blue-700">
                        {{ stats.running }}
                    </div>
                </div>
                <div class="bg-green-50 rounded-lg p-3">
                    <div class="text-sm font-medium text-green-600">Завершены</div>
                    <div class="mt-1 text-2xl font-semibold text-green-700">
                        {{ stats.completed }}
                    </div>
                </div>
                <div class="bg-red-50 rounded-lg p-3">
                    <div class="text-sm font-medium text-red-600">Ошибки</div>
                    <div class="mt-1 text-2xl font-semibold text-red-700">
                        {{ stats.failed }}
                    </div>
                </div>
            </div>

            <!-- Фильтры -->
            <div class="flex space-x-4 mb-4">
                <select
                    v-model="selectedStatus"
                    @change="refreshTasks"
                    class="block w-32 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                >
                    <option value="">Все статусы</option>
                    <option value="pending">Ожидают</option>
                    <option value="running">Выполняются</option>
                    <option value="completed">Завершены</option>
                    <option value="failed">Ошибки</option>
                </select>
            </div>

            <!-- Список задач -->
            <div v-if="loading && tasks.length === 0" class="text-center py-8">
                <div
                    class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                <p class="mt-2 text-sm text-gray-500">Загрузка задач...</p>
            </div>

            <div v-else-if="tasks.length === 0" class="text-center py-8">
                <ExclamationCircleIcon class="mx-auto h-12 w-12 text-gray-400"/>
                <h3 class="mt-2 text-sm font-medium text-gray-900">Нет задач</h3>
                <p class="mt-1 text-sm text-gray-500">
                    Задачи нагула профилей будут отображены здесь
                </p>
            </div>

            <div v-else class="space-y-3">
                <div
                    v-for="task in tasks"
                    :key="task.task_id"
                    class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                >
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <!-- Статус и ID -->
                            <div class="flex items-center space-x-3 mb-2">
                                <span
                                    :class="getStatusBadgeClass(task.status)"
                                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                                >
                                    <span
                                        :class="getStatusDotClass(task.status)"
                                        class="w-1.5 h-1.5 rounded-full mr-1.5"
                                    ></span>
                                    {{ getStatusText(task.status) }}
                                </span>
                                <code class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                    {{ task.task_id.substring(0, 8) }}
                                </code>
                            </div>

                            <!-- Детали задачи -->
                            <div class="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span class="text-gray-500">Тип устройства:</span>
                                    <span class="ml-1 font-medium">{{ task.device_type }}</span>
                                </div>
                                <div>
                                    <span class="text-gray-500">Приоритет:</span>
                                    <span class="ml-1 font-medium">{{ task.priority }}</span>
                                </div>
                                <div>
                                    <span class="text-gray-500">Создана:</span>
                                    <span class="ml-1">{{ formatDate(task.created_at) }}</span>
                                </div>
                                <div v-if="task.completed_at">
                                    <span class="text-gray-500">Завершена:</span>
                                    <span class="ml-1">{{ formatDate(task.completed_at) }}</span>
                                </div>
                            </div>

                            <!-- Worker info -->
                            <div v-if="task.worker_id" class="mt-2 text-sm text-gray-600">
                                <span class="text-gray-500">Worker:</span>
                                <code class="ml-1 text-xs bg-gray-100 px-1 py-0.5 rounded">
                                    {{ task.worker_id }}
                                </code>
                            </div>

                            <!-- Ошибка -->
                            <div v-if="task.error_message"
                                 class="mt-2 p-2 bg-red-50 rounded text-sm text-red-700">
                                {{ task.error_message }}
                            </div>

                            <!-- Результат -->
                            <div v-if="task.result && task.status === 'completed'" class="mt-2">
                                <details class="text-sm">
                                    <summary
                                        class="cursor-pointer text-green-600 hover:text-green-700">
                                        Результат нагула
                                    </summary>
                                    <div class="mt-2 p-2 bg-green-50 rounded">
                                        <div class="grid grid-cols-2 gap-2">
                                            <div>
                                                <span class="text-gray-600">Куки собрано:</span>
                                                <span class="ml-1 font-medium">
                                                    {{ task.result.cookies_collected || 0 }}
                                                </span>
                                            </div>
                                            <div>
                                                <span class="text-gray-600">Сайтов посещено:</span>
                                                <span class="ml-1 font-medium">
                                                    {{ task.result.sites_visited || 0 }}
                                                </span>
                                            </div>
                                            <div>
                                                <span class="text-gray-600">Тип нагула:</span>
                                                <span class="ml-1 font-medium">
                                                    {{ task.result.nurture_type || 'unknown' }}
                                                </span>
                                            </div>
                                            <div v-if="task.result.profile_id">
                                                <span class="text-gray-600">Профиль:</span>
                                                <code
                                                    class="ml-1 text-xs bg-white px-1 py-0.5 rounded">
                                                    {{ task.result.profile_id.substring(0, 8) }}
                                                </code>
                                            </div>
                                        </div>
                                    </div>
                                </details>
                            </div>
                        </div>

                        <!-- Действия -->
                        <div class="flex space-x-2 ml-4">
                            <button
                                v-if="task.status === 'pending'"
                                @click="cancelTask(task.task_id)"
                                class="text-red-600 hover:text-red-700 text-sm font-medium"
                            >
                                Отменить
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Пагинация -->
            <div v-if="pagination && pagination.has_more" class="mt-6 text-center">
                <button
                    @click="loadMore"
                    :disabled="loading"
                    class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                    Загрузить еще
                </button>
            </div>
        </div>

        <!-- Модальное окно создания задач -->
        <CreateNurtureTasksModal
            v-if="showCreateTaskModal"
            :strategy-id="strategyId"
            @close="showCreateTaskModal = false"
            @created="handleTasksCreated"
        />
    </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, watch, onUnmounted} from 'vue'
import {
    ArrowPathIcon,
    PlusIcon,
    ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'
import {api} from '@/api'
import CreateNurtureTasksModal from './CreateNurtureTasksModal.vue'

interface Props {
    strategyId: string
}

const props = defineProps<Props>()

// Reactive data
const tasks = ref([])
const stats = ref(null)
const pagination = ref(null)
const loading = ref(false)
const selectedStatus = ref('')
const showCreateTaskModal = ref(false)

// Methods
const refreshTasks = async () => {
    loading.value = true
    try {
        const response = await api.getProfileNurtureTasks(props.strategyId, {
            limit: 20,
            offset: 0,
            status: selectedStatus.value || undefined,
        })

        console.log(response)

        if (response.success) {
            tasks.value = response.tasks
            stats.value = response.stats
            pagination.value = response.pagination
        }
    } catch (error) {
        console.error('Error loading tasks:', error)
    } finally {
        loading.value = false
    }
}

const loadMore = async () => {
    if (!pagination.value?.has_more || loading.value) return

    loading.value = true
    try {
        const response = await api.getProfileNurtureTasks(props.strategyId, {
            limit: 20,
            offset: pagination.value.offset + 20,
            status: selectedStatus.value || undefined,
        })

        if (response.data.success) {
            tasks.value.push(...response.data.tasks)
            pagination.value = response.data.pagination
        }
    } catch (error) {
        console.error('Error loading more tasks:', error)
    } finally {
        loading.value = false
    }
}

const cancelTask = async (taskId: string) => {
    if (!confirm('Вы уверены, что хотите отменить эту задачу?')) return

    try {
        const response = await api.cancelNurtureTask(props.strategyId, taskId)

        if (response.data.success) {
            await refreshTasks()
        }
    } catch (error) {
        console.error('Error cancelling task:', error)
    }
}

const handleTasksCreated = () => {
    showCreateTaskModal.value = false
    refreshTasks()
}

// Utility methods
const getStatusBadgeClass = (status: string) => {
    const classes: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-800',
        running: 'bg-blue-100 text-blue-800',
        completed: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800',
        cancelled: 'bg-gray-100 text-gray-800',
    }
    return classes[status] || 'bg-gray-100 text-gray-800'
}

const getStatusDotClass = (status: string) => {
    const classes: Record<string, string> = {
        pending: 'bg-yellow-400',
        running: 'bg-blue-400',
        completed: 'bg-green-400',
        failed: 'bg-red-400',
        cancelled: 'bg-gray-400',
    }
    return classes[status] || 'bg-gray-400'
}

const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
        pending: 'Ожидает',
        running: 'Выполняется',
        completed: 'Завершена',
        failed: 'Ошибка',
        cancelled: 'Отменена',
    }
    return texts[status] || status
}

const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

// Lifecycle
onMounted(() => {
    refreshTasks()

    // Автообновление каждые 30 секунд
    const interval = setInterval(refreshTasks, 30000)

    // Очищаем интервал при размонтировании
    onUnmounted(() => {
        clearInterval(interval)
    })
})

// Watchers
watch(() => props.strategyId, () => {
    refreshTasks()
})
watch(() => props.strategyId, (newStrategyId, oldStrategyId) => {
    console.log('Strategy ID changed from', oldStrategyId, 'to', newStrategyId)
    if (newStrategyId) {
        refreshTasks()
    }
}, {immediate: true})
onMounted(() => {
    console.log('ProfileNurtureTasksMonitor mounted with strategy:', props.strategyId)

    // Вызываем только если есть strategyId
    if (props.strategyId) {
        refreshTasks()
    }

    // Автообновление каждые 30 секунд
    const interval = setInterval(() => {
        if (props.strategyId) {
            console.log('Auto refresh for strategy:', props.strategyId)
            refreshTasks()
        }
    }, 30000)

    onUnmounted(() => {
        console.log('ProfileNurtureTasksMonitor unmounted')
        clearInterval(interval)
    })
})
</script>
