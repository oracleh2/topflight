<template>
    <Modal
        :isOpen="isOpen"
        title="Добавить домен"
        @close="$emit('close')"
    >
        <form @submit.prevent="handleSubmit">
            <div class="space-y-4">
                <div>
                    <label for="domain" class="block text-sm font-medium text-gray-700">
                        Домен
                    </label>
                    <input
                        id="domain"
                        v-model="form.domain"
                        type="text"
                        class="input mt-1"
                        :class="{ 'border-red-500': errors.domain }"
                        placeholder="example.com"
                        @input="clearError('domain')"
                    />
                    <p v-if="errors.domain" class="mt-1 text-sm text-red-600">
                        {{ errors.domain }}
                    </p>
                    <p class="mt-1 text-xs text-gray-500">
                        Введите домен без http:// и www.
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
                    <p class="mt-1 text-xs text-gray-500">
                        Все ключевые слова этого домена будут проверяться в выбранном регионе
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
import {reactive, ref, onMounted} from 'vue'
import {MagnifyingGlassIcon, XMarkIcon} from '@heroicons/vue/24/outline'
import {useDomainsStore} from '@/stores/domains'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
    isOpen: boolean
}

interface Emits {
    (e: 'close'): void

    (e: 'success', domainId: string): void
}

interface Region {
    id: string
    code: string
    name: string
    region_type?: string
    country_code?: string
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const domainsStore = useDomainsStore()

const form = reactive({
    domain: '',
    regionId: ''
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

    if (!form.domain.trim()) {
        errors.value.domain = 'Домен обязателен'
    } else {
        // Простая валидация домена
        const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.([a-zA-Z]{2,}\.)*[a-zA-Z]{2,}$/
        const cleanDomain = form.domain.trim().toLowerCase()
            .replace(/^https?:\/\//, '')
            .replace(/^www\./, '')
            .replace(/\/$/, '')

        if (!domainRegex.test(cleanDomain)) {
            errors.value.domain = 'Некорректный формат домена'
        } else {
            form.domain = cleanDomain
        }
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
        const result = await domainsStore.addDomain(form.domain, form.regionId)

        // Сбрасываем форму
        form.domain = ''
        form.regionId = ''
        errors.value = {}

        // Очищаем поиск регионов
        clearSelectedRegion()

        emit('success', result.domain_id)
    } catch (error) {
        console.error('Error adding domain:', error)
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
