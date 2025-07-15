<!-- frontend/src/components/strategies/DataSourceImport.vue -->
<template>
    <div class="border border-gray-200 rounded-lg p-4">
        <h4 class="text-sm font-medium text-gray-900 mb-3">{{ title }}</h4>
        <p class="text-xs text-gray-500 mb-4">{{ description }}</p>

        <div class="space-y-4">
            <!-- Тип источника -->
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Способ импорта данных
                </label>
                <div class="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    <div
                        v-for="sourceType in sourceTypes"
                        :key="sourceType.value"
                        class="relative"
                    >
                        <input
                            :id="`source-${sourceType.value}-${componentId}`"
                            v-model="source.type"
                            :value="sourceType.value"
                            type="radio"
                            class="sr-only peer"
                            @change="handleSourceTypeChange"
                        >
                        <label
                            :for="`source-${sourceType.value}-${componentId}`"
                            class="flex items-center justify-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50 peer-checked:border-primary-600 peer-checked:bg-primary-50 peer-checked:text-primary-600 cursor-pointer"
                        >
                            <component :is="sourceType.icon" class="h-4 w-4 mr-2"/>
                            {{ sourceType.label }}
                        </label>
                    </div>
                </div>
            </div>

            <!-- URL для внешних источников -->
            <div v-if="needsUrl" class="space-y-3">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        {{ getUrlLabel() }}
                    </label>
                    <div class="flex space-x-2">
                        <input
                            v-model="source.source_url"
                            type="url"
                            :placeholder="getUrlPlaceholder()"
                            class="flex-1 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                        >
                        <button
                            type="button"
                            @click="handleTest"
                            :disabled="!source.source_url || testing"
                            class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {{ testing ? 'Тест...' : 'Тест' }}
                        </button>
                    </div>
                    <p class="mt-1 text-xs text-gray-500">
                        {{ getUrlDescription() }}
                    </p>
                </div>

                <!-- Опция обновления для URL источников -->
                <div v-if="allowRefresh && source.type === 'url_endpoint'">
                    <label class="flex items-center">
                        <input
                            v-model="source.refresh_on_each_cycle"
                            type="checkbox"
                            class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        >
                        <span class="ml-2 text-sm text-gray-700">
                            Обновлять данные на каждом цикле
                        </span>
                    </label>
                    <p class="mt-1 text-xs text-gray-500">
                        Если включено, данные будут загружаться заново при каждом запуске
                    </p>
                </div>
            </div>

            <!-- Загрузка файла -->
            <div v-if="source.type === 'file_upload'" class="space-y-3">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Загрузить файл
                    </label>
                    <div class="flex items-center space-x-3">
                        <input
                            ref="fileInput"
                            type="file"
                            accept=".txt,.csv"
                            @change="handleFileUpload"
                            class="hidden"
                        >
                        <button
                            type="button"
                            @click="$refs.fileInput.click()"
                            class="flex items-center px-4 py-2 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                        >
                            <DocumentIcon class="h-4 w-4 mr-2"/>
                            Выбрать файл
                        </button>
                        <span v-if="uploadedFileName" class="text-sm text-gray-600">
                            {{ uploadedFileName }}
                        </span>
                    </div>
                    <p class="mt-1 text-xs text-gray-500">
                        Поддерживаемые форматы: .txt, .csv (один элемент на строку)
                    </p>
                </div>

                <!-- Предпросмотр загруженного файла -->
                <div v-if="source.data_content" class="space-y-2">
                    <label class="block text-sm font-medium text-gray-700">
                        Предпросмотр ({{ getItemsCount() }} элементов)
                    </label>
                    <div
                        class="bg-gray-50 border border-gray-200 rounded-md p-3 max-h-40 overflow-y-auto">
                        <div class="text-xs text-gray-600 font-mono whitespace-pre-wrap">
                            {{ getPreview() }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Ручной ввод -->
            <div v-if="source.type === 'manual_input'" class="space-y-3">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Введите данные (один элемент на строку)
                    </label>
                    <textarea
                        v-model="source.data_content"
                        rows="8"
                        :placeholder="placeholder"
                        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 font-mono text-sm"
                    ></textarea>
                    <div class="flex justify-between items-center mt-1">
                        <p class="text-xs text-gray-500">
                            Каждый элемент на новой строке
                        </p>
                        <span class="text-xs text-gray-500">
                            {{ getItemsCount() }} элементов
                        </span>
                    </div>
                </div>
            </div>

            <!-- Статистика -->
            <div v-if="source.data_content || source.source_url" class="bg-gray-50 rounded-md p-3">
                <div class="flex items-center justify-between">
                    <div class="text-sm text-gray-600">
                        <span class="font-medium">{{ getItemsCount() }}</span> элементов загружено
                    </div>
                    <div class="flex items-center space-x-2">
                        <span
                            :class="[
                                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                                getStatusClass()
                            ]"
                        >
                            {{ getStatusText() }}
                        </span>
                        <button
                            v-if="canClearData"
                            @click="clearData"
                            class="text-xs text-red-600 hover:text-red-500"
                        >
                            Очистить
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, computed, watch} from 'vue'
import {
    DocumentIcon,
    DocumentTextIcon,
    LinkIcon,
    TableCellsIcon,
    GlobeAltIcon,
    PencilIcon
} from '@heroicons/vue/24/outline'

interface DataSource {
    type: string
    source_url?: string
    data_content?: string
    refresh_on_each_cycle: boolean
}

const props = withDefaults(defineProps<{
    modelValue: DataSource
    title: string
    description: string
    placeholder: string
    allowRefresh: boolean
    strategyId?: string
}>(), {
    allowRefresh: true,
    strategyId: undefined
})

const emit = defineEmits<{
    'update:modelValue': [value: DataSource]
    'test': [data: any]
}>()

const componentId = ref(Math.random().toString(36).substr(2, 9))
const uploadedFileName = ref('')
const testing = ref(false)

const source = computed({
    get: () => props.modelValue,
    set: (value: DataSource) => emit('update:modelValue', value)
})

const sourceTypes = [
    {
        value: 'manual_input',
        label: 'Ручной ввод',
        icon: PencilIcon
    },
    {
        value: 'file_upload',
        label: 'Загрузка файла',
        icon: DocumentIcon
    },
    {
        value: 'url_endpoint',
        label: 'URL источник',
        icon: GlobeAltIcon
    },
    {
        value: 'google_sheets',
        label: 'Google Таблицы',
        icon: TableCellsIcon
    },
    {
        value: 'google_docs',
        label: 'Google Документы',
        icon: DocumentTextIcon
    }
]

const needsUrl = computed(() => {
    return ['url_endpoint', 'google_sheets', 'google_docs'].includes(source.value.type)
})

const canClearData = computed(() => {
    return source.value.data_content || source.value.source_url
})

function getUrlLabel(): string {
    switch (source.value.type) {
        case 'url_endpoint':
            return 'URL источника'
        case 'google_sheets':
            return 'Ссылка на Google Таблицу'
        case 'google_docs':
            return 'Ссылка на Google Документ'
        default:
            return 'URL'
    }
}

function getUrlPlaceholder(): string {
    switch (source.value.type) {
        case 'url_endpoint':
            return 'https://example.com/keywords.txt'
        case 'google_sheets':
            return 'https://docs.google.com/spreadsheets/d/...'
        case 'google_docs':
            return 'https://docs.google.com/document/d/...'
        default:
            return 'https://example.com'
    }
}

function getUrlDescription(): string {
    switch (source.value.type) {
        case 'url_endpoint':
            return 'URL должен возвращать текст с элементами по одному на строку'
        case 'google_sheets':
            return 'Ссылка на публичную Google Таблицу'
        case 'google_docs':
            return 'Ссылка на публичный Google Документ'
        default:
            return ''
    }
}

function getItemsCount(): number {
    if (!source.value.data_content) return 0
    return source.value.data_content.split('\n').filter(line => line.trim()).length
}

function getPreview(): string {
    if (!source.value.data_content) return ''
    const lines = source.value.data_content.split('\n').filter(line => line.trim())
    return lines.slice(0, 10).join('\n') + (lines.length > 10 ? '\n...' : '')
}

function getStatusClass(): string {
    const count = getItemsCount()
    if (count === 0) return 'bg-gray-100 text-gray-800'
    if (count < 10) return 'bg-yellow-100 text-yellow-800'
    return 'bg-green-100 text-green-800'
}

function getStatusText(): string {
    const count = getItemsCount()
    if (count === 0) return 'Пусто'
    if (count < 10) return 'Мало данных'
    return 'Готово'
}

function handleSourceTypeChange() {
    // Очищаем данные при смене типа источника
    source.value.source_url = ''
    source.value.data_content = ''
    source.value.refresh_on_each_cycle = false
    uploadedFileName.value = ''
}

async function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]

    if (!file) return

    uploadedFileName.value = file.name

    try {
        const content = await readFileContent(file)
        source.value.data_content = content
    } catch (error) {
        console.error('Error reading file:', error)
        // Здесь можно показать уведомление об ошибке
    }
}

function readFileContent(file: File): Promise<string> {
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

function handleTest() {
    testing.value = true

    emit('test', {
        source_type: source.value.type,
        source_url: source.value.source_url,
        data_content: source.value.data_content
    })

    // Сбрасываем состояние тестирования через 3 секунды
    setTimeout(() => {
        testing.value = false
    }, 3000)
}

function clearData() {
    source.value.data_content = ''
    source.value.source_url = ''
    uploadedFileName.value = ''
}

// Инициализация значений по умолчанию
watch(() => props.modelValue, (newValue) => {
    if (!newValue.type) {
        source.value.type = 'manual_input'
    }
    if (newValue.refresh_on_each_cycle === undefined) {
        source.value.refresh_on_each_cycle = false
    }
}, {immediate: true})
</script>
