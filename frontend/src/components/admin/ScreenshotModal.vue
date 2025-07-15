<!-- frontend/src/components/admin/ScreenshotModal.vue -->
<template>
    <Modal
        :isOpen="isOpen"
        title="Скриншот debug сессии"
        panel-class="max-w-6xl"
        @close="$emit('close')"
    >
        <div v-if="loading" class="flex justify-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>

        <div v-else-if="screenshotUrl" class="space-y-4">
            <!-- Screenshot Controls -->
            <div class="flex items-center justify-between bg-gray-50 rounded-lg p-4">
                <div class="flex items-center space-x-4">
                    <span class="text-sm font-medium text-gray-700">Task ID: {{ taskId }}</span>
                    <span class="text-sm text-gray-500">{{ formatTime(screenshotTime) }}</span>
                </div>
                <div class="flex space-x-2">
                    <button
                        @click="refreshScreenshot"
                        :disabled="refreshing"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                    >
                        <svg v-if="refreshing"
                             class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none"
                             viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                    stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor"
                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Обновить
                    </button>
                    <button
                        @click="downloadScreenshot"
                        class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                    >
                        Скачать
                    </button>
                    <button
                        @click="openInNewTab"
                        class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                    >
                        Открыть в новой вкладке
                    </button>
                </div>
            </div>

            <!-- Screenshot -->
            <div class="bg-gray-100 rounded-lg p-4 overflow-auto max-h-[70vh]">
                <img
                    :src="screenshotUrl"
                    :alt="`Screenshot of task ${taskId}`"
                    class="max-w-full h-auto rounded border border-gray-300 shadow-lg"
                    @load="onImageLoad"
                    @error="onImageError"
                />
            </div>

            <!-- Auto-refresh Controls -->
            <div class="flex items-center justify-between bg-gray-50 rounded-lg p-4">
                <div class="flex items-center space-x-4">
                    <label class="flex items-center">
                        <input
                            type="checkbox"
                            v-model="autoRefresh"
                            class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                        >
                        <span class="ml-2 text-sm text-gray-700">Автообновление</span>
                    </label>

                    <select
                        v-model="refreshInterval"
                        :disabled="!autoRefresh"
                        class="text-sm border-gray-300 rounded-md disabled:opacity-50"
                    >
                        <option :value="5000">5 секунд</option>
                        <option :value="10000">10 секунд</option>
                        <option :value="30000">30 секунд</option>
                        <option :value="60000">1 минута</option>
                    </select>
                </div>

                <div class="text-sm text-gray-500">
                    Последнее обновление: {{ formatTime(screenshotTime) }}
                </div>
            </div>
        </div>

        <div v-else-if="error" class="text-center py-12">
            <div class="text-red-600 mb-4">
                <svg class="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24"
                     stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.316 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                </svg>
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">Не удалось загрузить скриншот</h3>
            <p class="text-gray-600 mb-4">{{ error }}</p>
            <button
                @click="loadScreenshot"
                class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
                Попробовать снова
            </button>
        </div>

        <div v-else class="text-center py-12 text-gray-500">
            Debug сессия не найдена или скриншот недоступен
        </div>
    </Modal>
</template>

<script setup lang="ts">
import {ref, watch, onUnmounted} from 'vue'
import {useToast} from '@/composables/useToast'
import Modal from '@/components/ui/Modal.vue'
import {api} from '@/api'  // ← Используем ваш API клиент

interface Props {
    isOpen: boolean
    taskId: string
}

const props = defineProps<Props>()
const emit = defineEmits(['close'])

const loading = ref(false)
const refreshing = ref(false)
const screenshotUrl = ref('')
const screenshotTime = ref(new Date())
const error = ref('')
const autoRefresh = ref(false)
const refreshInterval = ref(10000)
const refreshTimer = ref(null)

const {showToast} = useToast()

const loadScreenshot = async () => {
    if (!props.taskId) return

    try {
        loading.value = true
        error.value = ''

        const response = await api.getDebugScreenshot(props.taskId)

        // Создаем URL для blob
        const blob = new Blob([response.data], {type: 'image/png'})

        // Очищаем предыдущий URL если есть
        if (screenshotUrl.value) {
            URL.revokeObjectURL(screenshotUrl.value)
        }

        screenshotUrl.value = URL.createObjectURL(blob)
        screenshotTime.value = new Date()

    } catch (err: any) {
        console.error('Failed to load screenshot:', err)
        error.value = err.response?.data?.detail || 'Ошибка загрузки скриншота'
    } finally {
        loading.value = false
    }
}

const refreshScreenshot = async () => {
    refreshing.value = true
    await loadScreenshot()
    refreshing.value = false
}

const downloadScreenshot = () => {
    if (!screenshotUrl.value) return

    const link = document.createElement('a')
    link.href = screenshotUrl.value
    link.download = `debug-screenshot-${props.taskId}-${Date.now()}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}

const openInNewTab = () => {
    if (screenshotUrl.value) {
        window.open(screenshotUrl.value, '_blank')
    }
}

const toggleAutoRefresh = () => {
    autoRefresh.value = !autoRefresh.value

    if (autoRefresh.value) {
        refreshTimer.value = setInterval(refreshScreenshot, refreshInterval.value)
    } else {
        if (refreshTimer.value) {
            clearInterval(refreshTimer.value)
            refreshTimer.value = null
        }
    }
}

const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })
}

// Watch for modal open/close
watch(() => props.isOpen, (newValue) => {
    if (newValue && props.taskId) {
        loadScreenshot()
    } else {
        // Очищаем таймер при закрытии
        if (refreshTimer.value) {
            clearInterval(refreshTimer.value)
            refreshTimer.value = null
        }
        autoRefresh.value = false

        // Очищаем URL для освобождения памяти
        if (screenshotUrl.value) {
            URL.revokeObjectURL(screenshotUrl.value)
            screenshotUrl.value = ''
        }

        error.value = ''
    }
})

// Cleanup on unmount
onUnmounted(() => {
    if (refreshTimer.value) {
        clearInterval(refreshTimer.value)
    }
    if (screenshotUrl.value) {
        URL.revokeObjectURL(screenshotUrl.value)
    }
})
</script>
