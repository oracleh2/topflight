<template>
    <Modal
        :isOpen="isOpen"
        title="Добавить ключевое слово"
        panel-class="max-w-lg"
        @close="$emit('close')"
    >
        <form @submit.prevent="handleSubmit">
            <div class="space-y-4">
                <div>
                    <label for="keyword" class="block text-sm font-medium text-gray-700">
                        Ключевое слово
                    </label>
                    <input
                        id="keyword"
                        v-model="form.keyword"
                        type="text"
                        class="input mt-1"
                        :class="{ 'border-red-500': errors.keyword }"
                        placeholder="Введите ключевое слово"
                        @input="clearError('keyword')"
                    />
                    <p v-if="errors.keyword" class="mt-1 text-sm text-red-600">
                        {{ errors.keyword }}
                    </p>
                </div>

                <div>
                    <label for="region" class="block text-sm font-medium text-gray-700">
                        Регион
                    </label>
                    <div class="relative mt-1">
                        <input
                            id="region"
                            v-model="regionSearch"
                            type="text"
                            class="input pr-10"
                            :class="{ 'border-red-500': errors.regionId }"
                            placeholder="Поиск по названию или коду (мин. 2 символа)"
                            @input="handleRegionSearch"
                            @focus="showRegionDropdown = true"
                            @blur="handleRegionBlur"
                        />
                        <div
                            class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                            <MagnifyingGlassIcon class="h-5 w-5 text-gray-400"/>
                        </div>

                        <!-- Dropdown с результатами поиска -->
                        <div
                            v-if="showRegionDropdown && regionSearch.length >= 2"
                            class="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
                        >
                            <div v-if="regionSearchLoading" class="p-3 text-center text-gray-500">
                                <Spinner class="inline mr-2 h-4 w-4"/>
                                Поиск...
                            </div>

                            <div v-else-if="regionSearchResults.length === 0"
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
                                    <div class="flex items-center justify-between">
                                        <span class="text-sm font-medium text-gray-900"
                                              v-html="highlightMatch(region.name, regionSearch)"></span>
                                        <span class="text-xs text-gray-500"
                                              v-html="highlightMatch(region.code, regionSearch)"></span>
                                    </div>
                                    <div v-if="region.region_type"
                                         class="text-xs text-gray-400 mt-1">
                                        {{ getRegionTypeLabel(region.region_type) }}
                                    </div>
                                </button>
                            </div>
                        </div>

                        <!-- Показать выбранный регион -->
                        <div v-if="selectedRegion"
                             class="mt-2 p-2 bg-gray-50 rounded border text-sm">
                            <div class="flex items-center justify-between">
                                <span class="font-medium">{{ selectedRegion.name }}</span>
                                <div class="flex items-center space-x-2">
                                    <span class="text-gray-500">{{ selectedRegion.code }}</span>
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
                    <p v-if="errors.regionId" class="mt-1 text-sm text-red-600">
                        {{ errors.regionId }}
                    </p>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700">
                        Тип устройства
                    </label>
                    <div class="mt-2 space-y-2">
                        <label class="flex items-center">
                            <input
                                v-model="form.deviceType"
                                type="radio"
                                value="desktop"
                                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                            />
                            <span class="ml-2 text-sm text-gray-700 flex items-center">
                                <ComputerDesktopIcon class="mr-1 h-4 w-4"/>
                                Десктоп
                            </span>
                        </label>
                        <label class="flex items-center">
                            <input
                                v-model="form.deviceType"
                                type="radio"
                                value="mobile"
                                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                            />
                            <span class="ml-2 text-sm text-gray-700 flex items-center">
                                <DevicePhoneMobileIcon class="mr-1 h-4 w-4"/>
                                Мобильный
                            </span>
                        </label>
                    </div>
                </div>

                <div>
                    <label for="frequency" class="block text-sm font-medium text-gray-700">
                        Частота проверки
                    </label>
                    <select
                        id="frequency"
                        v-model="form.checkFrequency"
                        class="input mt-1"
                    >
                        <option value="daily">Ежедневно</option>
                        <option value="weekly">Еженедельно</option>
                        <option value="monthly">Ежемесячно</option>
                    </select>
                </div>

                <div>
                    <label class="flex items-center">
                        <input
                            v-model="form.isActive"
                            type="checkbox"
                            class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <span class="ml-2 text-sm text-gray-700">
                            Активное ключевое слово
                        </span>
                    </label>
                    <p class="mt-1 text-sm text-gray-500">
                        Неактивные ключевые слова не будут проверяться
                    </p>
                </div>
            </div>

            <Alert
                v-if="domainsStore.error"
                type="error"
                :message="domainsStore.error"
                class="mt-4"
                dismissible
                @dismiss="domainsStore.error = null"
            />
        </form>

        <template #actions>
            <button
                type="button"
                class="btn-secondary"
                @click="$emit('close')"
            >
                Отмена
            </button>
            <button
                type="button"
                class="btn-primary ml-3"
                @click="handleSubmit"
                :disabled="domainsStore.loading"
            >
                <Spinner v-if="domainsStore.loading" class="mr-2 h-4 w-4"/>
                Добавить
            </button>
        </template>
    </Modal>
</template>

<script setup lang="ts">
import {onMounted, reactive, ref, nextTick} from 'vue'
import {
    ComputerDesktopIcon,
    DevicePhoneMobileIcon,
    MagnifyingGlassIcon,
    XMarkIcon
} from '@heroicons/vue/24/outline'
import {useDomainsStore} from '@/stores/domains'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
    isOpen: boolean
    domainId: string
}

interface Emits {
    (e: 'close'): void

    (e: 'success'): void
}

interface Region {
    id: string
    code: string
    name: string
    region_type?: string
    country_code?: string
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const domainsStore = useDomainsStore()

const form = reactive({
    keyword: '',
    regionId: '',
    deviceType: 'desktop',
    checkFrequency: 'daily',
    isActive: true
})

const errors = ref<Record<string, string>>({})

// Поиск регионов
const regionSearch = ref('')
const regionSearchResults = ref<Region[]>([])
const regionSearchLoading = ref(false)
const showRegionDropdown = ref(false)
const selectedRegion = ref<Region | null>(null)

// Debounce для поиска
let searchTimeout: ReturnType<typeof setTimeout> | null = null

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
            const results = await domainsStore.searchRegions(query)
            regionSearchResults.value = results
        } catch (error) {
            console.error('Error searching regions:', error)
            regionSearchResults.value = []
        } finally {
            regionSearchLoading.value = false
        }
    }, 300) // Задержка 300ms для debounce
}

const selectRegion = (region: Region) => {
    selectedRegion.value = region
    form.regionId = region.id
    regionSearch.value = region.name
    showRegionDropdown.value = false
    clearError('regionId')
}

const clearSelectedRegion = () => {
    selectedRegion.value = null
    form.regionId = ''
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

const validateForm = () => {
    errors.value = {}

    if (!form.keyword.trim()) {
        errors.value.keyword = 'Ключевое слово обязательно'
    }

    if (!form.regionId) {
        errors.value.regionId = 'Регион обязателен'
    }

    return Object.keys(errors.value).length === 0
}

const clearError = (field: string) => {
    if (errors.value[field]) {
        delete errors.value[field]
    }
}

const handleSubmit = async () => {
    if (!validateForm()) {
        return
    }

    try {
        await domainsStore.addKeyword(
            props.domainId,
            form.keyword.trim(),
            form.regionId,
            form.deviceType,
            form.checkFrequency,
            form.isActive
        )

        // Сбрасываем форму
        form.keyword = ''
        form.regionId = ''
        form.deviceType = 'desktop'
        form.checkFrequency = 'daily'
        form.isActive = true
        errors.value = {}

        // Очищаем поиск регионов
        clearSelectedRegion()

        emit('success')
    } catch (error) {
        console.error('Error adding keyword:', error)
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
