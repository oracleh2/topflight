<!-- frontend/src/components/strategies/AddStrategyProxyModal.vue -->
<template>
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">
                    Добавить прокси к стратегии
                </h3>
            </div>

            <div class="p-6">
                <!-- Выбор типа импорта -->
                <div class="mb-6">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Способ импорта
                    </label>
                    <div class="grid grid-cols-2 gap-3">
                        <button
                            v-for="type in importTypes"
                            :key="type.value"
                            @click="selectedImportType = type.value"
                            :class="[
                                'p-4 border-2 rounded-lg text-left transition-colors',
                                selectedImportType === type.value
                                    ? 'border-primary-500 bg-primary-50'
                                    : 'border-gray-200 hover:border-gray-300'
                            ]"
                        >
                            <div class="flex items-center">
                                <component :is="type.icon" class="h-5 w-5 mr-2"/>
                                <div>
                                    <p class="font-medium">{{ type.label }}</p>
                                    <p class="text-sm text-gray-500">{{ type.description }}</p>
                                </div>
                            </div>
                        </button>
                    </div>
                </div>

                <!-- Форма ввода в зависимости от типа -->
                <div v-if="selectedImportType === 'manual_list'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Прокси (построчно)
                    </label>
                    <textarea
                        v-model="manualProxyText"
                        rows="10"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="192.168.1.1:8080:username:password
192.168.1.2:3128
socks5://192.168.1.3:1080:user:pass"
                    ></textarea>
                    <p class="text-xs text-gray-500 mt-1">
                        Поддерживаемые форматы: host:port, host:port:user:pass,
                        protocol://host:port:user:pass
                    </p>
                </div>

                <div v-if="selectedImportType === 'file_upload'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Выберите файл
                    </label>
                    <input
                        ref="fileInput"
                        type="file"
                        accept=".txt,.csv"
                        @change="handleFileSelect"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                    <p class="text-xs text-gray-500 mt-1">
                        Поддерживаемые форматы: .txt, .csv
                    </p>
                </div>

                <div v-if="selectedImportType === 'url_import'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        URL для импорта
                    </label>
                    <input
                        v-model="importUrl"
                        type="url"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="https://example.com/proxies.txt"
                    >
                    <p class="text-xs text-gray-500 mt-1">
                        URL должен возвращать список прокси в текстовом формате
                    </p>
                </div>

                <div v-if="selectedImportType === 'google_docs'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Ссылка на Google Документ
                    </label>
                    <input
                        v-model="googleDocUrl"
                        type="url"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="https://docs.google.com/document/d/..."
                    >
                    <p class="text-xs text-gray-500 mt-1">
                        Документ должен быть доступен для чтения по ссылке
                    </p>
                </div>

                <div v-if="selectedImportType === 'google_sheets'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Ссылка на Google Таблицы
                    </label>
                    <input
                        v-model="googleSheetsUrl"
                        type="url"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="https://docs.google.com/spreadsheets/d/..."
                    >
                    <p class="text-xs text-gray-500 mt-1">
                        Таблица должна быть доступна для чтения по ссылке
                    </p>
                </div>

                <!-- Результат импорта -->
                <div v-if="importResult" class="mt-4 p-4 rounded-lg" :class="[
                    importResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                ]">
                    <div class="flex items-center">
                        <CheckCircleIcon v-if="importResult.success"
                                         class="h-5 w-5 text-green-500 mr-2"/>
                        <XCircleIcon v-else class="h-5 w-5 text-red-500 mr-2"/>
                        <p class="text-sm font-medium" :class="[
                            importResult.success ? 'text-green-800' : 'text-red-800'
                        ]">
                            {{
                                importResult.success ? 'Импорт завершен успешно' : 'Ошибка импорта'
                            }}
                        </p>
                    </div>
                    <div v-if="importResult.success" class="mt-2 text-sm text-green-700">
                        <p>Обработано: {{ importResult.total_parsed }}</p>
                        <p>Успешно импортировано: {{ importResult.successfully_imported }}</p>
                        <p v-if="importResult.failed_imports > 0">Ошибок:
                            {{ importResult.failed_imports }}</p>
                    </div>
                    <div v-if="importResult.errors && importResult.errors.length > 0" class="mt-2">
                        <p class="text-sm font-medium text-red-800">Ошибки:</p>
                        <ul class="mt-1 text-sm text-red-700">
                            <li v-for="error in importResult.errors" :key="error">{{ error }}</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                    @click="$emit('close')"
                    class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                    Отмена
                </button>
                <button
                    @click="importProxies"
                    :disabled="loading || !canImport"
                    class="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-400"
                >
                    <span v-if="loading">
                        <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white inline"
                             xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                    stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor"
                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Импорт...
                    </span>
                    <span v-else>
                        Импортировать
                    </span>
                </button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, computed} from 'vue'
import {
    DocumentTextIcon,
    ArrowUpTrayIcon,
    LinkIcon,
    DocumentIcon,
    TableCellsIcon,
    CheckCircleIcon,
    XCircleIcon
} from '@heroicons/vue/24/outline'
import {useStrategiesStore} from '@/stores/strategies'
import {api} from '@/api'


// Props
interface Props {
    strategyId: string
}

const props = defineProps<Props>()
// Store
const strategiesStore = useStrategiesStore()

// Emits
const emit = defineEmits<{
    close: []
    success: []
}>()

// Reactive data
const loading = ref(false)
const selectedImportType = ref('manual_list')
const manualProxyText = ref('')
const importUrl = ref('')
const googleDocUrl = ref('')
const googleSheetsUrl = ref('')
const selectedFile = ref<File | null>(null)
const importResult = ref<any>(null)

// Computed
const importTypes = computed(() => [
    {
        value: 'manual_list',
        label: 'Ручной ввод',
        description: 'Вставить прокси в текстовом формате',
        icon: DocumentTextIcon
    },
    {
        value: 'file_upload',
        label: 'Файл',
        description: 'Загрузить файл с прокси',
        icon: ArrowUpTrayIcon
    },
    {
        value: 'url_import',
        label: 'URL импорт',
        description: 'Импорт по ссылке',
        icon: LinkIcon
    },
    {
        value: 'google_docs',
        label: 'Google Документы',
        description: 'Импорт из Google Docs',
        icon: DocumentIcon
    },
    {
        value: 'google_sheets',
        label: 'Google Таблицы',
        description: 'Импорт из Google Sheets',
        icon: TableCellsIcon
    }
])

const canImport = computed(() => {
    switch (selectedImportType.value) {
        case 'manual_list':
            return manualProxyText.value.trim().length > 0
        case 'file_upload':
            return selectedFile.value !== null
        case 'url_import':
            return importUrl.value.trim().length > 0
        case 'google_docs':
            return googleDocUrl.value.trim().length > 0
        case 'google_sheets':
            return googleSheetsUrl.value.trim().length > 0
        default:
            return false
    }
})

// Methods
const handleFileSelect = (event: Event) => {
    const target = event.target as HTMLInputElement
    selectedFile.value = target.files?.[0] || null
}

const importProxies = async () => {
    if (!canImport.value) return

    loading.value = true
    importResult.value = null

    try {
        let result: any

        switch (selectedImportType.value) {
            case 'manual_list':
                result = await api.importStrategyProxiesManual(props.strategyId, manualProxyText.value)
                break

            case 'file_upload':
                if (!selectedFile.value) return
                result = await api.importStrategyProxiesFile(props.strategyId, selectedFile.value)
                break

            case 'url_import':
                result = await api.importStrategyProxiesUrl(props.strategyId, importUrl.value)
                break

            case 'google_docs':
                result = await api.importStrategyProxiesGoogleDoc(props.strategyId, googleDocUrl.value)
                break

            case 'google_sheets':
                result = await api.importStrategyProxiesGoogleSheets(props.strategyId, googleSheetsUrl.value)
                break

            default:
                throw new Error('Неподдерживаемый тип импорта')
        }

        importResult.value = result.data

        if (result.data.success) {
            setTimeout(() => {
                emit('success')
            }, 1500)
        }

    } catch (error) {
        console.error('Error importing proxies:', error)
        importResult.value = {
            success: false,
            errors: ['Ошибка при импорте прокси']
        }
    } finally {
        loading.value = false
    }
}
</script>
