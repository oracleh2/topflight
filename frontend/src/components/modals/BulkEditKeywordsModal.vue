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
                                            Массовое редактирование ключевых слов
                                        </DialogTitle>
                                        <p class="mt-1 text-sm text-gray-500">
                                            Редактируйте ключевые слова в текстовом поле
                                        </p>
                                    </div>
                                    <button
                                        @click="$emit('close')"
                                        class="text-gray-400 hover:text-gray-500"
                                    >
                                        <XMarkIcon class="h-6 w-6"/>
                                    </button>
                                </div>

                                <div class="space-y-6">
                                    <!-- Textarea для редактирования -->
                                    <div>
                                        <div class="flex items-center justify-between mb-2">
                                            <label class="block text-sm font-medium text-gray-700">
                                                Ключевые слова (каждое с новой строки)
                                            </label>
                                            <div class="flex space-x-2">
                                                <button
                                                    @click="selectAll"
                                                    class="text-sm text-primary-600 hover:text-primary-500"
                                                >
                                                    Выделить все
                                                </button>
                                                <button
                                                    @click="clearAll"
                                                    class="text-sm text-red-600 hover:text-red-500"
                                                >
                                                    Очистить
                                                </button>
                                            </div>
                                        </div>
                                        <textarea
                                            ref="textareaRef"
                                            v-model="keywordsText"
                                            rows="15"
                                            class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                            placeholder="Вставьте или отредактируйте ключевые слова..."
                                            @input="updateKeywordsList"
                                            @keydown.ctrl.a.prevent="selectAll"
                                            @keydown.ctrl.v.prevent="handlePaste"
                                        />
                                        <div
                                            class="mt-2 flex items-center justify-between text-sm text-gray-500">
                                            <span>Обнаружено ключевых слов: <strong>{{
                                                    parsedKeywords.length
                                                }}</strong></span>
                                            <div class="flex space-x-4">
                        <span v-if="originalKeywords.length > 0">
                          Было: {{ originalKeywords.length }}
                        </span>
                                                <span v-if="addedKeywords.length > 0"
                                                      class="text-green-600">
                          Добавлено: {{ addedKeywords.length }}
                        </span>
                                                <span v-if="removedKeywords.length > 0"
                                                      class="text-red-600">
                          Удалено: {{ removedKeywords.length }}
                        </span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Статистика изменений -->
                                    <div v-if="hasChanges"
                                         class="bg-blue-50 border border-blue-200 rounded-md p-4">
                                        <div class="flex">
                                            <InformationCircleIcon class="h-5 w-5 text-blue-400"/>
                                            <div class="ml-3">
                                                <h3 class="text-sm font-medium text-blue-800">
                                                    Изменения будут применены
                                                </h3>
                                                <div class="mt-2 text-sm text-blue-700">
                                                    <div v-if="addedKeywords.length > 0"
                                                         class="mb-1">
                                                        <strong>Добавлено ({{
                                                                addedKeywords.length
                                                            }}):</strong>
                                                        <div class="mt-1 max-h-20 overflow-y-auto">
                                                            <div class="flex flex-wrap gap-1">
                                <span
                                    v-for="keyword in addedKeywords.slice(0, 10)"
                                    :key="keyword"
                                    class="inline-block bg-green-100 text-green-800 px-2 py-1 rounded text-xs"
                                >
                                  {{ keyword }}
                                </span>
                                                                <span
                                                                    v-if="addedKeywords.length > 10"
                                                                    class="text-xs text-green-600">
                                  ... и еще {{ addedKeywords.length - 10 }}
                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div v-if="removedKeywords.length > 0">
                                                        <strong>Удалено ({{
                                                                removedKeywords.length
                                                            }}):</strong>
                                                        <div class="mt-1 max-h-20 overflow-y-auto">
                                                            <div class="flex flex-wrap gap-1">
                                <span
                                    v-for="keyword in removedKeywords.slice(0, 10)"
                                    :key="keyword"
                                    class="inline-block bg-red-100 text-red-800 px-2 py-1 rounded text-xs"
                                >
                                  {{ keyword }}
                                </span>
                                                                <span
                                                                    v-if="removedKeywords.length > 10"
                                                                    class="text-xs text-red-600">
                                  ... и еще {{ removedKeywords.length - 10 }}
                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Настройки для новых ключевых слов -->
                                    <div v-if="addedKeywords.length > 0"
                                         class="bg-gray-50 border border-gray-200 rounded-md p-4">
                                        <h4 class="text-sm font-medium text-gray-900 mb-3">
                                            Настройки для новых ключевых слов
                                        </h4>
                                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
                                                        class="block w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 pr-8"
                                                        placeholder="Поиск региона..."
                                                        @input="handleRegionSearch"
                                                        @focus="showRegionDropdown = true"
                                                        @blur="handleRegionBlur"
                                                    />
                                                    <div
                                                        class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                                                        <MagnifyingGlassIcon
                                                            class="h-4 w-4 text-gray-400"/>
                                                    </div>

                                                    <!-- Dropdown с результатами поиска -->
                                                    <div
                                                        v-if="showRegionDropdown && regionSearch.length >= 2"
                                                        class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-40 overflow-auto"
                                                    >
                                                        <div v-if="regionSearchLoading"
                                                             class="p-2 text-center text-gray-500 text-sm">
                                                            <div
                                                                class="flex items-center justify-center">
                                                                <svg
                                                                    class="animate-spin h-3 w-3 mr-1"
                                                                    viewBox="0 0 24 24">
                                                                    <circle cx="12" cy="12" r="10"
                                                                            stroke="currentColor"
                                                                            stroke-width="4"
                                                                            fill="none"
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
                                                            class="p-2 text-center text-gray-500 text-sm">
                                                            Регионы не найдены
                                                        </div>

                                                        <div v-else>
                                                            <button
                                                                v-for="region in regionSearchResults"
                                                                :key="region.id"
                                                                type="button"
                                                                class="w-full px-2 py-1 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none text-sm"
                                                                @click="selectRegion(region)"
                                                            >
                                                                <div
                                                                    class="flex items-center justify-between">
                                                                    <span class="font-medium">{{
                                                                            region.name
                                                                        }}</span>
                                                                    <span
                                                                        class="text-xs text-gray-500">{{
                                                                            region.code
                                                                        }}</span>
                                                                </div>
                                                            </button>
                                                        </div>
                                                    </div>

                                                    <!-- Показать выбранный регион -->
                                                    <div v-if="selectedRegion"
                                                         class="mt-1 p-1 bg-gray-100 rounded text-xs">
                                                        <div
                                                            class="flex items-center justify-between">
                                                            <span>{{ selectedRegion.name }}</span>
                                                            <button
                                                                type="button"
                                                                class="text-gray-400 hover:text-gray-600"
                                                                @click="clearSelectedRegion"
                                                            >
                                                                <XMarkIcon class="h-3 w-3"/>
                                                            </button>
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
                                                    class="block w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                                >
                                                    <option value="desktop">Десктоп</option>
                                                    <option value="mobile">Мобильный</option>
                                                    <option value="tablet">Планшет</option>
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
                                                    class="block w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                                                >
                                                    <option value="daily">Ежедневно</option>
                                                    <option value="weekly">Еженедельно</option>
                                                    <option value="monthly">Ежемесячно</option>
                                                </select>
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
                                    @click="applyChanges"
                                    :disabled="!hasChanges || applying || (addedKeywords.length > 0 && !selectedRegion)"
                                    class="btn-primary"
                                >
                                    {{ applying ? 'Применение...' : 'Применить изменения' }}
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
import {ref, computed, onMounted, watch, nextTick} from 'vue'
import {
    Dialog,
    DialogPanel,
    DialogTitle,
    TransitionChild,
    TransitionRoot,
} from '@headlessui/vue'
import {
    XMarkIcon,
    InformationCircleIcon,
    ExclamationTriangleIcon,
    MagnifyingGlassIcon,
} from '@heroicons/vue/24/outline'
import {api} from '@/api'

interface Props {
    isOpen: boolean
    domainId: string
    keywords: KeywordData[]
}

interface KeywordData {
    id: string
    keyword: string
    region: {
        id: string
        code: string
        name: string
    }
    device_type: string
    check_frequency: string
    is_active: boolean
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
    success: [changes: { added: string[], removed: string[] }]
}>()

// State
const keywordsText = ref('')
const originalKeywords = ref<string[]>([])
const textareaRef = ref<HTMLTextAreaElement>()
const applying = ref(false)
const error = ref('')

// Region search
const regionSearch = ref('')
const regionSearchResults = ref<Region[]>([])
const regionSearchLoading = ref(false)
const showRegionDropdown = ref(false)
const selectedRegion = ref<Region | null>(null)

// Settings for new keywords
const selectedDeviceType = ref('desktop')
const selectedCheckFrequency = ref('daily')

// Debounce для поиска
let searchTimeout: ReturnType<typeof setTimeout> | null = null

// Computed
const parsedKeywords = computed(() => {
    return keywordsText.value
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
})

const addedKeywords = computed(() => {
    return parsedKeywords.value.filter(keyword =>
        !originalKeywords.value.includes(keyword)
    )
})

const removedKeywords = computed(() => {
    return originalKeywords.value.filter(keyword =>
        !parsedKeywords.value.includes(keyword)
    )
})

const hasChanges = computed(() => {
    return addedKeywords.value.length > 0 || removedKeywords.value.length > 0
})

// Initialize keywords when modal opens
watch(() => props.isOpen, (isOpen) => {
    if (isOpen && props.keywords.length > 0) {
        const keywords = props.keywords.map(k => k.keyword)
        originalKeywords.value = [...keywords]
        keywordsText.value = keywords.join('\n')
    }
})

// Methods
const updateKeywordsList = () => {
    // This is called on textarea input
}

const selectAll = () => {
    nextTick(() => {
        if (textareaRef.value) {
            textareaRef.value.select()
        }
    })
}

const clearAll = () => {
    keywordsText.value = ''
}

const handlePaste = async (event: Event) => {
    const clipboardEvent = event as ClipboardEvent
    const text = clipboardEvent.clipboardData?.getData('text')
    if (text) {
        // Handle paste event
        const textarea = textareaRef.value
        if (textarea) {
            const start = textarea.selectionStart
            const end = textarea.selectionEnd
            const currentText = keywordsText.value
            keywordsText.value = currentText.substring(0, start) + text + currentText.substring(end)

            // Set cursor position
            nextTick(() => {
                const newPosition = start + text.length
                textarea.setSelectionRange(newPosition, newPosition)
            })
        }
    }
}

const handleRegionSearch = async () => {
    const query = regionSearch.value.trim()

    if (query.length < 2) {
        regionSearchResults.value = []
        return
    }

    if (searchTimeout) {
        clearTimeout(searchTimeout)
    }

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
    selectedRegion.value = region
    regionSearch.value = region.name
    showRegionDropdown.value = false
}

const clearSelectedRegion = () => {
    selectedRegion.value = null
    regionSearch.value = ''
    regionSearchResults.value = []
}

const handleRegionBlur = () => {
    setTimeout(() => {
        showRegionDropdown.value = false
    }, 200)
}

const applyChanges = async () => {
    if (!hasChanges.value) return

    applying.value = true
    error.value = ''

    try {
        const changes = {
            added: addedKeywords.value,
            removed: removedKeywords.value
        }

        // Apply changes via API
        await api.bulkEditKeywords(props.domainId, {
            added_keywords: addedKeywords.value,
            removed_keywords: removedKeywords.value.map(keyword => {
                const keywordData = props.keywords.find(k => k.keyword === keyword)
                return keywordData?.id || ''
            }).filter(id => id !== ''),
            new_keywords_settings: addedKeywords.value.length > 0 ? {
                region_id: selectedRegion.value?.id || '',
                device_type: selectedDeviceType.value,
                check_frequency: selectedCheckFrequency.value,
                is_active: true
            } : undefined
        })

        emit('success', changes)
        emit('close')
    } catch (err: any) {
        error.value = err.response?.data?.detail || 'Ошибка при применении изменений'
    } finally {
        applying.value = false
    }
}

onMounted(() => {
    return () => {
        if (searchTimeout) {
            clearTimeout(searchTimeout)
        }
    }
})
</script>
