<!-- frontend/src/components/modals/AddDataSourceModal.vue -->
<template>
    <TransitionRoot as="template" :show="isOpen">
        <Dialog as="div" class="relative z-10" @close="$emit('close')">
            <TransitionChild
                as="template"
                enter="ease-out duration-300"
                enter-from="opacity-0"
                enter-to="opacity-100"
                leave="ease-in duration-200"
                leave-from="opacity-100"
                leave-to="opacity-0"
            >
                <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"/>
            </TransitionChild>

            <div class="fixed inset-0 z-10 overflow-y-auto">
                <div
                    class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <TransitionChild
                        as="template"
                        enter="ease-out duration-300"
                        enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
                        enter-to="opacity-100 translate-y-0 sm:scale-100"
                        leave="ease-in duration-200"
                        leave-from="opacity-100 translate-y-0 sm:scale-100"
                        leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
                    >
                        <DialogPanel
                            class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                            <form @submit.prevent="handleSubmit">
                                <div>
                                    <div
                                        class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
                                        <DocumentIcon class="h-6 w-6 text-primary-600"
                                                      aria-hidden="true"/>
                                    </div>
                                    <div class="mt-3 text-center sm:mt-5">
                                        <DialogTitle as="h3"
                                                     class="text-base font-semibold leading-6 text-gray-900">
                                            Добавить источник данных
                                        </DialogTitle>
                                        <div class="mt-2">
                                            <p class="text-sm text-gray-500">
                                                Добавьте данные для стратегии "{{ strategy?.name }}"
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div class="mt-6 space-y-6">
                                    <!-- Тип источника -->
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Тип источника данных *
                                        </label>
                                        <select
                                            v-model="form.source_type"
                                            required
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            @change="resetFormData"
                                        >
                                            <option value="">Выберите тип источника</option>
                                            <option value="manual_list">Ручной ввод</option>
                                            <option value="file_upload">Загрузка файла</option>
                                            <option value="url_import">Импорт по URL</option>
                                            <option value="google_sheets">Google Таблицы</option>
                                            <option value="google_docs">Google Документы</option>
                                        </select>
                                    </div>

                                    <!-- Ручной ввод -->
                                    <div v-if="form.source_type === 'manual_list'">
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Данные (каждая строка - новый элемент) *
                                        </label>
                                        <textarea
                                            v-model="form.data_content"
                                            rows="6"
                                            required
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            placeholder="Введите данные, каждый элемент с новой строки..."
                                        ></textarea>
                                        <p class="mt-1 text-xs text-gray-500">
                                            Каждая строка будет считаться отдельным элементом данных
                                        </p>
                                    </div>

                                    <!-- Загрузка файла -->
                                    <div v-if="form.source_type === 'file_upload'">
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Выберите файл *
                                        </label>
                                        <input
                                            ref="fileInput"
                                            type="file"
                                            accept=".txt,.csv"
                                            @change="handleFileSelect"
                                            class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                                        />
                                        <p class="mt-1 text-xs text-gray-500">
                                            Поддерживаются форматы: .txt, .csv
                                        </p>

                                        <!-- Предварительный просмотр файла -->
                                        <div v-if="filePreview"
                                             class="mt-3 p-3 bg-gray-50 rounded-md">
                                            <h5 class="text-sm font-medium text-gray-900 mb-2">
                                                Предварительный просмотр:</h5>
                                            <div
                                                class="text-xs text-gray-600 max-h-32 overflow-y-auto">
                                                <div
                                                    v-for="(item, index) in filePreview.slice(0, 10)"
                                                    :key="index">
                                                    {{ item }}
                                                </div>
                                                <div v-if="filePreview.length > 10"
                                                     class="text-gray-500 mt-1">
                                                    ... и еще {{ filePreview.length - 10 }}
                                                    элементов
                                                </div>
                                            </div>
                                            <p class="text-xs text-gray-500 mt-2">
                                                Всего элементов: {{ filePreview.length }}
                                            </p>
                                        </div>
                                    </div>

                                    <!-- Импорт по URL -->
                                    <div v-if="form.source_type === 'url_import'">
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            URL для импорта *
                                        </label>
                                        <input
                                            v-model="form.source_url"
                                            type="url"
                                            required
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            placeholder="https://example.com/data.txt"
                                        />
                                        <p class="mt-1 text-xs text-gray-500">
                                            Укажите прямую ссылку на файл с данными (.txt или .csv)
                                        </p>
                                    </div>

                                    <!-- Google Таблицы -->
                                    <div v-if="form.source_type === 'google_sheets'">
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Ссылка на Google Таблицу *
                                        </label>
                                        <input
                                            v-model="form.source_url"
                                            type="url"
                                            required
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            placeholder="https://docs.google.com/spreadsheets/d/..."
                                        />
                                        <p class="mt-1 text-xs text-gray-500">
                                            Убедитесь, что доступ к таблице открыт для просмотра
                                        </p>
                                    </div>

                                    <!-- Google Документы -->
                                    <div v-if="form.source_type === 'google_docs'">
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Ссылка на Google Документ *
                                        </label>
                                        <input
                                            v-model="form.source_url"
                                            type="url"
                                            required
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            placeholder="https://docs.google.com/document/d/..."
                                        />
                                        <p class="mt-1 text-xs text-gray-500">
                                            Убедитесь, что доступ к документу открыт для просмотра
                                        </p>
                                    </div>

                                    <!-- Дополнительные настройки -->
                                    <div v-if="form.source_type" class="border-t pt-4">
                                        <h4 class="text-sm font-medium text-gray-900 mb-3">
                                            Дополнительные настройки</h4>

                                        <div class="space-y-3">
                                            <label class="flex items-center">
                                                <input
                                                    v-model="form.is_active"
                                                    type="checkbox"
                                                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                                />
                                                <span class="ml-2 text-sm text-gray-700">Активный источник данных</span>
                                            </label>

                                            <div
                                                v-if="form.source_type === 'url_import' || form.source_type === 'google_sheets' || form.source_type === 'google_docs'">
                                                <label class="flex items-center">
                                                    <input
                                                        v-model="form.auto_update"
                                                        type="checkbox"
                                                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                                    />
                                                    <span class="ml-2 text-sm text-gray-700">Автоматически обновлять данные</span>
                                                </label>
                                                <p class="ml-6 text-xs text-gray-500">
                                                    Данные будут обновляться автоматически из
                                                    источника
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="mt-6 flex justify-end space-x-3">
                                    <button
                                        type="button"
                                        class="btn-secondary"
                                        @click="$emit('close')"
                                    >
                                        Отмена
                                    </button>
                                    <button
                                        type="submit"
                                        class="btn-primary"
                                        :disabled="loading || !isFormValid"
                                    >
                                        <Spinner v-if="loading" class="w-4 h-4 mr-2"/>
                                        Добавить источник
                                    </button>
                                </div>
                            </form>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>
</template>

<script setup lang="ts">
import {ref, computed, watch} from 'vue'
import {Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot} from '@headlessui/vue'
import {DocumentIcon} from '@heroicons/vue/24/outline'

import {useStrategiesStore} from '@/stores/strategies'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
    isOpen: boolean
    strategy: any | null
}

interface Emits {
    (e: 'close'): void

    (e: 'added', dataSource: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const strategiesStore = useStrategiesStore()

const loading = ref(false)
const fileInput = ref<HTMLInputElement>()
const selectedFile = ref<File | null>(null)
const filePreview = ref<string[]>([])

const form = ref({
    source_type: '',
    source_url: '',
    data_content: '',
    is_active: true,
    auto_update: false
})

const isFormValid = computed(() => {
    if (!form.value.source_type) return false

    switch (form.value.source_type) {
        case 'manual_list':
            return !!form.value.data_content.trim()
        case 'file_upload':
            return !!selectedFile.value
        case 'url_import':
        case 'google_sheets':
        case 'google_docs':
            return !!form.value.source_url.trim()
        default:
            return false
    }
})

function resetForm() {
    form.value = {
        source_type: '',
        source_url: '',
        data_content: '',
        is_active: true,
        auto_update: false
    }
    selectedFile.value = null
    filePreview.value = []
    if (fileInput.value) {
        fileInput.value.value = ''
    }
}

function resetFormData() {
    form.value.source_url = ''
    form.value.data_content = ''
    selectedFile.value = null
    filePreview.value = []
    if (fileInput.value) {
        fileInput.value.value = ''
    }
}

async function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]

    if (!file) {
        selectedFile.value = null
        filePreview.value = []
        return
    }

    selectedFile.value = file

    // Читаем файл для предварительного просмотра
    try {
        const text = await file.text()
        const lines = text.split('\n').map(line => line.trim()).filter(line => line)

        if (file.name.endsWith('.csv')) {
            // Простой парсинг CSV
            const items: string[] = []
            lines.forEach(line => {
                const csvItems = line.split(',').map(item => item.trim().replace(/"/g, ''))
                items.push(...csvItems.filter(item => item))
            })
            filePreview.value = items
        } else {
            filePreview.value = lines
        }
    } catch (error) {
        console.error('Error reading file:', error)
        filePreview.value = []
    }
}

async function handleSubmit() {
    if (!props.strategy) return

    try {
        loading.value = true

        let dataSource

        if (form.value.source_type === 'file_upload' && selectedFile.value) {
            // Загружаем файл
            dataSource = await strategiesStore.uploadDataFile(props.strategy.id, selectedFile.value)
        } else {
            // Создаем источник данных
            dataSource = await strategiesStore.addDataSource(props.strategy.id, {
                source_type: form.value.source_type,
                source_url: form.value.source_url || undefined,
                data_content: form.value.data_content || undefined
            })
        }

        emit('added', dataSource)
        resetForm()
    } catch (error) {
        console.error('Error adding data source:', error)
        // Здесь можно добавить уведомление об ошибке
    } finally {
        loading.value = false
    }
}

// Сбрасываем форму при открытии модального окна
watch(() => props.isOpen, (isOpen) => {
    if (isOpen) {
        resetForm()
    }
})
</script>
