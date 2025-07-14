<!-- frontend/src/components/admin/VncInstructionsModal.vue -->
<template>
    <Modal
        :isOpen="isOpen"
        title="VNC подключение к debug сессии"
        panel-class="max-w-4xl"
        @close="$emit('close')"
    >
        <div v-if="loading" class="flex justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>

        <div v-else-if="instructions" class="space-y-6">
            <!-- Connection Info -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd"
                                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                                  clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-blue-800">
                            Информация о подключении
                        </h3>
                        <div class="mt-2 text-sm text-blue-700">
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <span class="font-medium">Task ID:</span> {{ taskId }}
                                </div>
                                <div>
                                    <span class="font-medium">VNC порт:</span>
                                    {{ instructions.vnc_connection.port }}
                                </div>
                                <div>
                                    <span class="font-medium">Хост:</span>
                                    {{ instructions.vnc_connection.host }}
                                </div>
                                <div>
                                    <span class="font-medium">VNC URL:</span>
                                    <code class="bg-blue-100 px-1 rounded text-xs">{{
                                            instructions.vnc_connection.url
                                        }}</code>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quick Commands -->
            <div class="space-y-4">
                <h4 class="text-lg font-medium text-gray-900">Команды для подключения</h4>

                <div class="space-y-3">
                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <h5 class="text-sm font-medium text-gray-900">VNC Viewer (локальное
                                подключение)</h5>
                            <button
                                @click="copyToClipboard(instructions.client_commands.vnc_viewer)"
                                class="text-sm text-blue-600 hover:text-blue-800"
                            >
                                Копировать
                            </button>
                        </div>
                        <code
                            class="block bg-gray-800 text-green-400 p-3 rounded text-sm font-mono">
                            {{ instructions.client_commands.vnc_viewer }}
                        </code>
                    </div>

                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <h5 class="text-sm font-medium text-gray-900">SSH туннель (удаленное
                                подключение)</h5>
                            <button
                                @click="copyToClipboard(instructions.client_commands.ssh_tunnel)"
                                class="text-sm text-blue-600 hover:text-blue-800"
                            >
                                Копировать
                            </button>
                        </div>
                        <code
                            class="block bg-gray-800 text-green-400 p-3 rounded text-sm font-mono">
                            {{ instructions.client_commands.ssh_tunnel }}
                        </code>
                        <p class="text-xs text-gray-600 mt-2">
                            Замените "user@your-server" на ваши учетные данные сервера
                        </p>
                    </div>

                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <h5 class="text-sm font-medium text-gray-900">Web VNC (в браузере)</h5>
                            <button
                                @click="copyToClipboard(instructions.client_commands.browser_vnc)"
                                class="text-sm text-blue-600 hover:text-blue-800"
                            >
                                Копировать
                            </button>
                        </div>
                        <code
                            class="block bg-gray-800 text-green-400 p-3 rounded text-sm font-mono">
                            {{ instructions.client_commands.browser_vnc }}
                        </code>
                        <p class="text-xs text-gray-600 mt-2">
                            Требует установленный noVNC сервер
                        </p>
                    </div>
                </div>
            </div>

            <!-- Recommended Clients -->
            <div class="space-y-4">
                <h4 class="text-lg font-medium text-gray-900">Рекомендуемые VNC клиенты</h4>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div
                        v-for="client in instructions.recommended_clients"
                        :key="client.name"
                        class="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                    >
                        <h5 class="font-medium text-gray-900 mb-2">{{ client.name }}</h5>
                        <p class="text-sm text-gray-600 mb-2">{{ client.platform }}</p>
                        <p v-if="client.description" class="text-xs text-gray-500 mb-3">
                            {{ client.description }}</p>
                        <a
                            v-if="client.download"
                            :href="client.download"
                            target="_blank"
                            class="text-sm text-blue-600 hover:text-blue-800 font-medium"
                        >
                            Скачать →
                        </a>
                    </div>
                </div>
            </div>

            <!-- Security Notes -->
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-yellow-400" fill="currentColor"
                             viewBox="0 0 20 20">
                            <path fill-rule="evenodd"
                                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                                  clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-medium text-yellow-800">
                            Важные замечания по безопасности
                        </h3>
                        <div class="mt-2 text-sm text-yellow-700">
                            <ul class="list-disc list-inside space-y-1">
                                <li v-for="note in instructions.security_notes" :key="note">
                                    {{ note }}
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Connection Test -->
            <div class="border-t pt-4">
                <button
                    @click="testConnection"
                    :disabled="testingConnection"
                    class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50"
                >
                    <svg v-if="testingConnection"
                         class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none"
                         viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Проверить VNC соединение
                </button>

                <div v-if="connectionTestResult" class="mt-3">
                    <div
                        :class="[
              'p-3 rounded-md text-sm',
              connectionTestResult.success
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            ]"
                    >
                        {{ connectionTestResult.message }}
                    </div>
                </div>
            </div>
        </div>

        <div v-else class="text-center py-8 text-gray-500">
            Не удалось загрузить инструкции по подключению
        </div>
    </Modal>
</template>

<script setup lang="ts">
import {ref, watch} from 'vue'
import {useToast} from '@/composables/useToast'
import Modal from '@/components/ui/Modal.vue'
import {api} from '@/api'

interface Props {
    isOpen: boolean
    taskId: string
}

const props = defineProps<Props>()
const emit = defineEmits(['close'])

const loading = ref(false)
const instructions = ref(null)
const testingConnection = ref(false)
const connectionTestResult = ref(null)

const {showToast} = useToast()

const loadInstructions = async () => {
    if (!props.taskId) return

    try {
        loading.value = true
        const response = await api.get(`/admin/debug/vnc-instructions/${props.taskId}`)
        instructions.value = response.data
    } catch (error) {
        console.error('Failed to load VNC instructions:', error)
        showToast('Ошибка загрузки инструкций VNC', 'error')
    } finally {
        loading.value = false
    }
}

const copyToClipboard = async (text: string) => {
    try {
        await navigator.clipboard.writeText(text)
        showToast('Команда скопирована в буфер обмена', 'success')
    } catch (error) {
        console.error('Failed to copy to clipboard:', error)
        showToast('Ошибка копирования в буфер обмена', 'error')
    }
}

const testConnection = async () => {
    try {
        testingConnection.value = true
        connectionTestResult.value = null

        const response = await api.get(`/admin/debug/session/${props.taskId}`)

        if (response.data.status === 'active') {
            connectionTestResult.value = {
                success: true,
                message: 'VNC сервер активен и готов к подключению'
            }
        } else {
            connectionTestResult.value = {
                success: false,
                message: 'VNC сервер неактивен или недоступен'
            }
        }
    } catch (error) {
        console.error('Connection test failed:', error)
        connectionTestResult.value = {
            success: false,
            message: 'Ошибка проверки соединения'
        }
    } finally {
        testingConnection.value = false
    }
}

// Watch for modal open/close
watch(() => props.isOpen, (newValue) => {
    if (newValue && props.taskId) {
        loadInstructions()
    } else {
        instructions.value = null
        connectionTestResult.value = null
    }
})
</script>
