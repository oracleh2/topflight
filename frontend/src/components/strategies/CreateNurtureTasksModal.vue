<!-- frontend/src/components/strategies/CreateNurtureTasksModal.vue -->
<template>
    <div class="fixed inset-0 z-50 overflow-y-auto">
        <div
            class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <!-- Overlay -->
            <div
                class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                @click="$emit('close')"
            ></div>

            <!-- Modal -->
            <div
                class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <form @submit.prevent="createTasks">
                    <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                        <div class="sm:flex sm:items-start">
                            <div
                                class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                                <PlusIcon class="h-6 w-6 text-blue-600"/>
                            </div>

                            <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                                <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                                    Создать задачи нагула
                                </h3>

                                <!-- Информация о стратегии -->
                                <div v-if="strategyStatus" class="mb-6 p-3 bg-gray-50 rounded-lg">
                                    <div class="text-sm text-gray-600 space-y-1">
                                        <div>
                                            <span class="font-medium">Текущее количество:</span>
                                            {{ strategyStatus.current_count }}
                                        </div>
                                        <div>
                                            <span class="font-medium">Минимум:</span>
                                            {{ strategyStatus.min_limit }}
                                        </div>
                                        <div>
                                            <span class="font-medium">Максимум:</span>
                                            {{ strategyStatus.max_limit }}
                                        </div>
                                        <div>
                                            <span class="font-medium">Нужно создать:</span>
                                            <span :class="neededTasksClass">
                                                {{
                                                    Math.max(0, strategyStatus.max_limit - strategyStatus.current_count)
                                                }}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Параметры создания -->
                                <div class="space-y-4">
                                    <!-- Количество задач -->
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Количество задач для создания
                                        </label>
                                        <input
                                            v-model.number="tasksCount"
                                            type="number"
                                            min="1"
                                            :max="maxTasksCount"
                                            required
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                            :placeholder="`Максимум: ${maxTasksCount}`"
                                        />
                                        <p class="mt-1 text-xs text-gray-500">
                                            Рекомендуемое количество: {{ suggestedTasksCount }}
                                        </p>
                                    </div>

                                    <!-- Приоритет -->
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Приоритет задач
                                        </label>
                                        <select
                                            v-model.number="priority"
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        >
                                            <option :value="1">Низкий (1)</option>
                                            <option :value="3">Ниже среднего (3)</option>
                                            <option :value="5">Средний (5)</option>
                                            <option :value="7">Выше среднего (7)</option>
                                            <option :value="10">Высокий (10)</option>
                                        </select>
                                    </div>

                                    <!-- Тип устройства -->
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Тип устройства
                                        </label>
                                        <select
                                            v-model="deviceType"
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                        >
                                            <option value="DESKTOP">Десктоп</option>
                                            <option value="MOBILE">Мобильный</option>
                                            <option value="TABLET">Планшет</option>
                                        </select>
                                    </div>

                                    <!-- Распределение по времени -->
                                    <div>
                                        <label class="flex items-center">
                                            <input
                                                v-model="distributeOverTime"
                                                type="checkbox"
                                                class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                                            />
                                            <span class="ml-2 text-sm text-gray-700">
                                                Распределить создание задач во времени
                                            </span>
                                        </label>
                                        <p class="mt-1 text-xs text-gray-500">
                                            Задачи будут создаваться постепенно, чтобы не
                                            перегружать систему
                                        </p>
                                    </div>
                                </div>

                                <!-- Предупреждения -->
                                <div v-if="warnings.length > 0" class="mt-4 space-y-2">
                                    <div
                                        v-for="warning in warnings"
                                        :key="warning"
                                        class="p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-700"
                                    >
                                        {{ warning }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                        <button
                            type="submit"
                            :disabled="loading || !canCreateTasks"
                            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <div v-if="loading"
                                 class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            {{ loading ? 'Создание...' : 'Создать задачи' }}
                        </button>

                        <button
                            type="button"
                            @click="$emit('close')"
                            :disabled="loading"
                            class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                        >
                            Отмена
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {PlusIcon} from '@heroicons/vue/24/outline'
import {api} from '@/api'

interface Props {
    strategyId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
    close: []
    created: [result: any]
}>()

// Reactive data
const strategyStatus = ref(null)
const loading = ref(false)
const tasksCount = ref(1)
const priority = ref(5)
const deviceType = ref('DESKTOP')
const distributeOverTime = ref(false)

// Computed
const maxTasksCount = computed(() => {
    if (!strategyStatus.value) return 50
    return Math.min(50, Math.max(0, strategyStatus.value.max_limit - strategyStatus.value.current_count))
})

const suggestedTasksCount = computed(() => {
    if (!strategyStatus.value) return 1
    return Math.min(10, Math.max(1, Math.ceil((strategyStatus.value.max_limit - strategyStatus.value.current_count) / 2)))
})

const neededTasksClass = computed(() => {
    if (!strategyStatus.value) return ''
    const needed = strategyStatus.value.max_limit - strategyStatus.value.current_count
    return needed > 0 ? 'text-blue-600 font-medium' : 'text-green-600 font-medium'
})

const canCreateTasks = computed(() => {
    return tasksCount.value > 0 && tasksCount.value <= maxTasksCount.value && !loading.value
})

const warnings = computed(() => {
    const warns = []

    if (!strategyStatus.value) return warns

    if (tasksCount.value > 20) {
        warns.push('Создание большого количества задач может замедлить систему')
    }

    if (strategyStatus.value.current_count >= strategyStatus.value.max_limit) {
        warns.push('Стратегия уже достигла максимального количества профилей')
    }

    if (priority.value >= 8) {
        warns.push('Высокий приоритет может замедлить выполнение других задач')
    }

    return warns
})

// Methods
const loadStrategyStatus = async () => {
    try {
        const response = await api.get(`/strategies/profile-nurture/${props.strategyId}/status`)
        if (response.data.success) {
            strategyStatus.value = response.data.status

            // Устанавливаем рекомендуемое количество задач
            tasksCount.value = suggestedTasksCount.value
        }
    } catch (error) {
        console.error('Error loading strategy status:', error)
    }
}

const createTasks = async () => {
    if (!canCreateTasks.value) return

    loading.value = true

    try {
        let result

        if (distributeOverTime.value && tasksCount.value > 5) {
            // Создаем задачи партиями
            result = await createTasksInBatches()
        } else {
            // Создаем все задачи сразу
            result = await createTasksBatch(tasksCount.value)
        }

        emit('created', result)
    } catch (error) {
        console.error('Error creating tasks:', error)
        alert('Ошибка при создании задач: ' + error.message)
    } finally {
        loading.value = false
    }
}

const createTasksBatch = async (count: number) => {
    // Создаем задачи через API нагула
    const response = await api.post(`/strategies/profile-nurture/${props.strategyId}/spawn-tasks`)

    if (!response.data.success) {
        throw new Error(response.data.message || 'Ошибка создания задач')
    }

    return response.data
}

const createTasksInBatches = async () => {
    const batchSize = 5
    const totalBatches = Math.ceil(tasksCount.value / batchSize)
    let totalCreated = 0

    for (let i = 0; i < totalBatches; i++) {
        const batchCount = Math.min(batchSize, tasksCount.value - totalCreated)

        // Создаем порцию задач
        const result = await createTasksBatch(batchCount)
        totalCreated += result.tasks_created || 0

        // Пауза между батчами (кроме последнего)
        if (i < totalBatches - 1) {
            await new Promise(resolve => setTimeout(resolve, 2000))
        }
    }

    return {
        success: true,
        message: `Создано ${totalCreated} задач в ${totalBatches} партиях`,
        tasks_created: totalCreated,
        batches: totalBatches,
    }
}

// Lifecycle
onMounted(() => {
    loadStrategyStatus()
})
</script>
