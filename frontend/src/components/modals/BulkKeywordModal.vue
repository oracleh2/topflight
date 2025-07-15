<template>
    <TransitionRoot as="template" :show="isOpen">
        <Dialog as="div" class="relative z-50" @close="$emit('close')">
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
                            class="relative transform overflow-hidden rounded-lg bg-white px-4 pt-5 pb-4 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl sm:p-6">
                            <div>
                                <div class="flex items-center justify-between mb-6">
                                    <div>
                                        <DialogTitle as="h3"
                                                     class="text-lg font-medium leading-6 text-gray-900">
                                            Массовое добавление ключевых слов
                                        </DialogTitle>
                                        <p class="mt-1 text-sm text-gray-500">
                                            Выберите способ добавления ключевых слов
                                        </p>
                                    </div>
                                    <button
                                        @click="$emit('close')"
                                        class="text-gray-400 hover:text-gray-500"
                                    >
                                        <XMarkIcon class="h-6 w-6"/>
                                    </button>
                                </div>

                                <!-- Method selection tabs -->
                                <div class="mb-6">
                                    <nav class="flex space-x-8" aria-label="Tabs">
                                        <button
                                            v-for="tab in tabs"
                                            :key="tab.id"
                                            @click="activeTab = tab.id"
                                            :class="[
                        activeTab === tab.id
                          ? 'border-primary-500 text-primary-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                        'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
                      ]"
                                        >
                                            <component :is="tab.icon" class="h-5 w-5 mr-2 inline"/>
                                            {{ tab.name }}
                                        </button>
                                    </nav>
                                </div>

                                <!-- Tab content -->
                                <div class="space-y-6">
                                    <!-- Textarea method -->
                                    <div v-if="activeTab === 'textarea'" class="space-y-4">
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                Ключевые слова (каждое с новой строки)
                                            </label>
                                            <textarea
                                                v-model="textareaContent"
                                                rows="10"
                                                class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                                placeholder="интернет магазин&#10;купить онлайн&#10;доставка товаров"
                                            />
                                            <p class="mt-1 text-sm text-gray-500">
                                                Каждое ключевое слово должно быть на отдельной
                                                строке
                                            </p>
                                        </div>
                                        <div class="bg-gray-50 p-4 rounded-md">
                                            <p class="text-sm text-gray-600">
                                                Обнаружено ключевых слов: <strong>{{
                                                    getKeywordsFromTextarea().length
                                                }}</strong>
                                            </p>
                                        </div>
                                    </div>

                                    <!-- Text file URL method -->
                                    <div v-if="activeTab === 'textfile'" class="space-y-4">
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                URL текстового файла
                                            </label>
                                            <input
                                                v-model="textFileUrl"
                                                type="url"
                                                class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                                placeholder="https://example.com/keywords.txt"
                                            />
                                            <p class="mt-1 text-sm text-gray-500">
                                                Файл должен содержать ключевые слова, каждое на
                                                новой строке
                                            </p>
                                        </div>
                                        <button
                                            @click="loadFromTextFile"
                                            :disabled="!textFileUrl || loading"
                                            class="btn-secondary"
                                        >
                                            <DocumentTextIcon class="h-4 w-4 mr-2"/>
                                            {{ loading ? 'Загрузка...' : 'Загрузить файл' }}
                                        </button>
                                    </div>

                                    <!-- Excel/Google Sheets method -->
                                    <div v-if="activeTab === 'excel'" class="space-y-4">
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                URL Excel файла или Google Sheets
                                            </label>
                                            <input
                                                v-model="excelUrl"
                                                type="url"
                                                class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                                placeholder="https://docs.google.com/spreadsheets/..."
                                            />
                                            <p class="mt-1 text-sm text-gray-500">
                                                Ключевые слова должны быть в первом столбце (A),
                                                каждое в отдельной строке
                                            </p>
                                        </div>
                                        <div class="grid grid-cols-2 gap-4">
                                            <div>
                                                <label
                                                    class="block text-sm font-medium text-gray-700 mb-1">
                                                    Номер листа
                                                </label>
                                                <input
                                                    v-model.number="excelSheet"
                                                    type="number"
                                                    min="1"
                                                    class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                                    placeholder="1"
                                                />
                                            </div>
                                            <div>
                                                <label
                                                    class="block text-sm font-medium text-gray-700 mb-1">
                                                    Начать со строки
                                                </label>
                                                <input
                                                    v-model.number="excelStartRow"
                                                    type="number"
                                                    min="1"
                                                    class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                                    placeholder="1"
                                                />
                                            </div>
                                        </div>
                                        <button
                                            @click="loadFromExcel"
                                            :disabled="!excelUrl || loading"
                                            class="btn-secondary"
                                        >
                                            <TableCellsIcon class="h-4 w-4 mr-2"/>
                                            {{ loading ? 'Загрузка...' : 'Загрузить из Excel' }}
                                        </button>
                                    </div>

                                    <!-- Word/Google Docs method -->
                                    <div v-if="activeTab === 'word'" class="space-y-4">
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                URL Word документа или Google Docs
                                            </label>
                                            <input
                                                v-model="wordUrl"
                                                type="url"
                                                class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                                placeholder="https://docs.google.com/document/..."
                                            />
                                            <p class="mt-1 text-sm text-gray-500">
                                                Каждое ключевое слово должно быть на отдельной
                                                строке документа
                                            </p>
                                        </div>
                                        <button
                                            @click="loadFromWord"
                                            :disabled="!wordUrl || loading"
                                            class="btn-secondary"
                                        >
                                            <DocumentIcon class="h-4 w-4 mr-2"/>
                                            {{ loading ? 'Загрузка...' : 'Загрузить из документа' }}
                                        </button>
                                    </div>

                                    <!-- Preview loaded keywords -->
                                    <div v-if="loadedKeywords.length > 0" class="mt-6">
                                        <div
                                            class="bg-green-50 border border-green-200 rounded-md p-4">
                                            <div class="flex">
                                                <CheckCircleIcon class="h-5 w-5 text-green-400"/>
                                                <div class="ml-3">
                                                    <h3 class="text-sm font-medium text-green-800">
                                                        Ключевые слова загружены
                                                    </h3>
                                                    <div class="mt-2 text-sm text-green-700">
                                                        <p>Найдено {{ loadedKeywords.length }}
                                                            ключевых слов:</p>
                                                        <div class="mt-2 max-h-40 overflow-y-auto">
                                                            <div class="text-xs space-y-1">
                                                                <div
                                                                    v-for="(keyword, index) in loadedKeywords.slice(0, 10)"
                                                                    :key="index"
                                                                    class="bg-white px-2 py-1 rounded border"
                                                                >
                                                                    {{ keyword }}
                                                                </div>
                                                                <div
                                                                    v-if="loadedKeywords.length > 10"
                                                                    class="text-center py-2">
                                                                    ... и еще
                                                                    {{ loadedKeywords.length - 10 }}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Error message -->
                                    <div v-if="error" class="mt-4">
                                        <div class="bg-red-50 border border-red-200 rounded-md p-4">
                                            <div class="flex">
                                                <ExclamationTriangleIcon
                                                    class="h-5 w-5 text-red-400"/>
                                                <div class="ml-3">
                                                    <h3 class="text-sm font-medium text-red-800">
                                                        Ошибка</h3>
                                                    <div class="mt-2 text-sm text-red-700">
                                                        <p>{{ error }}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Additional settings -->
                                <div class="mt-6 pt-6 border-t border-gray-200">
                                    <h4 class="text-sm font-medium text-gray-900 mb-4">
                                        Настройки</h4>
                                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <!-- Region Search -->
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-1">
                                                Регион
                                            </label>
                                            <div class="relative">
                                                <input
                                                    v-model="regionSearch"
                                                    type="text"
                                                    class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 pr-10"
                                                    :class="{ 'border-red-500': !selectedRegion && regionSearch }"
                                                    placeholder="Поиск по названию или коду (мин. 2 символа)"
                                                    @input="handleRegionSearch"
                                                    @focus="showRegionDropdown = true"
                                                    @blur="handleRegionBlur"
                                                />
                                                <div
                                                    class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                                                    <MagnifyingGlassIcon
                                                        class="h-5 w-5 text-gray-400"/>
                                                </div>

                                                <!-- Dropdown с результатами поиска -->
                                                <div
                                                    v-if="showRegionDropdown && regionSearch.length >= 2"
                                                    class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
                                                >
                                                    <div v-if="regionSearchLoading"
                                                         class="p-3 text-center text-gray-500">
                                                        <div
                                                            class="flex items-center justify-center">
                                                            <svg class="animate-spin h-4 w-4 mr-2"
                                                                 viewBox="0 0 24 24">
                                                                <circle cx="12" cy="12" r="10"
                                                                        stroke="currentColor"
                                                                        stroke-width="4" fill="none"
                                                                        opacity="0.25"/>
                                                                <path
                                                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                                                    fill="currentColor"/>
                                                            </svg>
                                                            Поиск...
                                                        </div>
                                                    </div>

                                                    <div
                                                        v-else-if="regionSearchResults.length === 0"
                                                        class="p-3 text-center text-gray-500">
                                                        Регионы не найдены
                                                    </div>

                                                    <div v-else>
                                                        <button
                                                            v-for="region in regionSearchResults"
                                                            :key="region.id"
                                                            type="button"
                                                            class="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none border-b border-gray-100 last:border-b-0"
                                                            @click="selectRegion(region)"
                                                        >
                                                            <div
                                                                class="flex items-center justify-between">
                                                                <span
                                                                    class="text-sm font-medium text-gray-900"
                                                                    v-html="highlightMatch(region.name, regionSearch)"></span>
                                                                <span class="text-xs text-gray-500"
                                                                      v-html="highlightMatch(region.code, regionSearch)"></span>
                                                            </div>
                                                            <div v-if="region.region_type"
                                                                 class="text-xs text-gray-400 mt-1">
                                                                {{
                                                                    getRegionTypeLabel(region.region_type)
                                                                }}
                                                            </div>
                                                        </button>
                                                    </div>
                                                </div>

                                                <!-- Показать выбранный регион -->
                                                <div v-if="selectedRegionObject"
                                                     class="mt-2 p-2 bg-gray-50 rounded border text-sm">
                                                    <div class="flex items-center justify-between">
                                                        <span class="font-medium">{{
                                                                selectedRegionObject.name
                                                            }}</span>
                                                        <div class="flex items-center space-x-2">
                                                            <span class="text-gray-500">{{
                                                                    selectedRegionObject.code
                                                                }}</span>
                                                            <button
                                                                type="button"
                                                                class="text-gray-400 hover:text-gray-600"
                                                                @click="clearSelectedRegion"
                                                            >
                                                                <XMarkIcon class="h-4 w-4"/>
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Device Type -->
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-1">
                                                Тип устройства
                                            </label>
                                            <select
                                                v-model="selectedDeviceType"
                                                class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                            >
                                                <option value="DESKTOP">Десктоп</option>
                                                <option value="MOBILE">Мобильный</option>
                                                <option value="TABLET">Планшет</option>
                                            </select>
                                        </div>

                                        <!-- Check Frequency -->
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-1">
                                                Частота проверки
                                            </label>
                                            <select
                                                v-model="selectedCheckFrequency"
                                                class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                            >
                                                <option value="daily">Ежедневно</option>
                                                <option value="weekly">Еженедельно</option>
                                                <option value="monthly">Ежемесячно</option>
                                            </select>
                                        </div>

                                        <!-- Is Active -->
                                        <div class="col-span-2">
                                            <label class="flex items-center">
                                                <input
                                                    v-model="selectedIsActive"
                                                    type="checkbox"
                                                    class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                                                />
                                                <span class="ml-2 text-sm text-gray-700">
                          Активные ключевые слова
                        </span>
                                            </label>
                                            <p class="mt-1 text-sm text-gray-500">
                                                Неактивные ключевые слова не будут проверяться
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Actions -->
                            <div class="mt-6 flex justify-end space-x-3">
                                <button
                                    @click="$emit('close')"
                                    class="btn-secondary"
                                >
                                    Отмена
                                </button>
                                <button
                                    @click="addKeywords"
                                    :disabled="!canAddKeywords || adding"
                                    class="btn-primary"
                                >
                                    {{
                                        adding ? 'Добавление...' : `Добавить ${finalKeywords.length} ключевых слов`
                                    }}
                                </button>
                            </div>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {
    Dialog,
    DialogPanel,
    DialogTitle,
    TransitionChild,
    TransitionRoot,
} from '@headlessui/vue'
import {
    XMarkIcon,
    DocumentTextIcon,
    TableCellsIcon,
    DocumentIcon,
    PencilSquareIcon,
    CheckCircleIcon,
    ExclamationTriangleIcon,
    MagnifyingGlassIcon,
} from '@heroicons/vue/24/outline'
import {api} from '@/api'

interface Props {
    isOpen: boolean
    domainId: string
}

interface Region {
    id: string
    code: string
    name: string
    region_type?: string
    country_code?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
    close: []
    success: [keywords: string[]]
}>()

// Tabs configuration
const tabs = [
    {id: 'textarea', name: 'Текст', icon: PencilSquareIcon},
    {id: 'textfile', name: 'Текстовый файл', icon: DocumentTextIcon},
    {id: 'excel', name: 'Excel/Sheets', icon: TableCellsIcon},
    {id: 'word', name: 'Word/Docs', icon: DocumentIcon},
]

// State
const activeTab = ref('textarea')
const loading = ref(false)
const adding = ref(false)
const error = ref('')

// Textarea method
const textareaContent = ref('')

// Text file method
const textFileUrl = ref('')

// Excel method
const excelUrl = ref('')
const excelSheet = ref(1)
const excelStartRow = ref(1)

// Word method
const wordUrl = ref('')

// Loaded keywords
const loadedKeywords = ref<string[]>([])

// Region search
const regionSearch = ref('')
const regionSearchResults = ref<Region[]>([])
const regionSearchLoading = ref(false)
const showRegionDropdown = ref(false)
const selectedRegionObject = ref<Region | null>(null)

// Settings
const selectedRegion = ref('')
const selectedDeviceType = ref('DESKTOP')
const selectedCheckFrequency = ref('daily')
const selectedIsActive = ref(true)

// Debounce для поиска
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// Computed
const finalKeywords = computed(() => {
    if (activeTab.value === 'textarea') {
        return getKeywordsFromTextarea()
    }
    return loadedKeywords.value
})

const canAddKeywords = computed(() => {
    return finalKeywords.value.length > 0 && selectedRegion.value
})

// Methods
const getKeywordsFromTextarea = () => {
    return textareaContent.value
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
}

const handleRegionSearch = async () => {
    const query = regionSearch.value.trim()

    if (query.length < 2) {
        regionSearchResults.value = []
        return
    }

    // Очищаем предыдущий таймаут
    if (searchTimeout) {
        clearTimeout(searchTimeout)
    }

    // Устанавливаем новый таймаут
    searchTimeout = setTimeout(async () => {
        regionSearchLoading.value = true

        try {
            const response = await api.searchRegions(query)
            regionSearchResults.value = response.data
        } catch (error) {
            console.error('Error searching regions:', error)
            regionSearchResults.value = []
        } finally {
            regionSearchLoading.value = false
        }
    }, 300)
}

const selectRegion = (region: Region) => {
    selectedRegionObject.value = region
    selectedRegion.value = region.id
    regionSearch.value = region.name
    showRegionDropdown.value = false
}

const clearSelectedRegion = () => {
    selectedRegionObject.value = null
    selectedRegion.value = ''
    regionSearch.value = ''
    regionSearchResults.value = []
}

const handleRegionBlur = () => {
    // Задержка для обработки клика по элементу dropdown
    setTimeout(() => {
        showRegionDropdown.value = false
    }, 200)
}

const getRegionTypeLabel = (type: string): string => {
    const types: Record<string, string> = {
        'city': 'Город',
        'region': 'Регион',
        'country': 'Страна'
    }
    return types[type] || type
}

const highlightMatch = (text: string, query: string): string => {
    if (!query || query.length < 2) return escapeHtml(text)

    const escapedText = escapeHtml(text)
    const escapedQuery = escapeHtml(query)
    const regex = new RegExp(`(${escapedQuery})`, 'gi')
    return escapedText.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>')
}

const escapeHtml = (text: string): string => {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
}

const loadFromTextFile = async () => {
    loading.value = true
    error.value = ''

    try {
        const response = await api.loadKeywordsFromTextFile(textFileUrl.value)
        loadedKeywords.value = response.data.keywords
    } catch (err: any) {
        error.value = err.response?.data?.detail || 'Ошибка загрузки файла'
    } finally {
        loading.value = false
    }
}

const loadFromExcel = async () => {
    loading.value = true
    error.value = ''

    try {
        const response = await api.loadKeywordsFromExcel(
            excelUrl.value,
            excelSheet.value,
            excelStartRow.value
        )
        loadedKeywords.value = response.data.keywords
    } catch (err: any) {
        error.value = err.response?.data?.detail || 'Ошибка загрузки Excel файла'
    } finally {
        loading.value = false
    }
}

const loadFromWord = async () => {
    loading.value = true
    error.value = ''

    try {
        const response = await api.loadKeywordsFromWord(wordUrl.value)
        loadedKeywords.value = response.data.keywords
    } catch (err: any) {
        error.value = err.response?.data?.detail || 'Ошибка загрузки Word документа'
    } finally {
        loading.value = false
    }
}

const addKeywords = async () => {
    adding.value = true
    error.value = ''

    try {
        const response = await api.addBulkKeywords(
            props.domainId,
            finalKeywords.value,
            selectedRegion.value,
            selectedDeviceType.value,
            selectedCheckFrequency.value,
            selectedIsActive.value
        )

        emit('success', finalKeywords.value)
        emit('close')
    } catch (err: any) {
        error.value = err.response?.data?.detail || 'Ошибка добавления ключевых слов'
    } finally {
        adding.value = false
    }
}

// Очищаем таймаут при размонтировании
onMounted(() => {
    return () => {
        if (searchTimeout) {
            clearTimeout(searchTimeout)
        }
    }
})
</script>
