<!-- frontend/src/components/strategies/ProfileNurtureForm.vue -->
<template>
    <div class="space-y-6">
        <!-- Тип нагула -->
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Тип нагула профиля
            </label>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div
                    v-for="type in nurtureTypes"
                    :key="type.value"
                    class="relative"
                >
                    <input
                        :id="`nurture-type-${type.value}`"
                        v-model="config.nurture_type"
                        :value="type.value"
                        type="radio"
                        class="sr-only peer"
                    >
                    <label
                        :for="`nurture-type-${type.value}`"
                        class="flex items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-900 hover:bg-gray-50 peer-checked:border-primary-600 peer-checked:bg-primary-50 peer-checked:text-primary-600 cursor-pointer"
                    >
                        <div class="text-center">
                            <div class="font-medium">{{ type.label }}</div>
                            <div class="text-xs text-gray-500 mt-1">{{ type.description }}</div>
                        </div>
                    </label>
                </div>
            </div>
        </div>

        <!-- Целевое количество куков -->
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Минимум куков
                </label>
                <input
                    v-model.number="config.target_cookies.min"
                    type="number"
                    min="1"
                    max="500"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Максимум куков
                </label>
                <input
                    v-model.number="config.target_cookies.max"
                    type="number"
                    min="1"
                    max="500"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
            </div>
        </div>

        <!-- Лимиты нагуленных профилей -->
        <div class="space-y-4">
            <h5 class="text-sm font-medium text-gray-900 flex items-center">
                <UsersIcon class="h-4 w-4 mr-2 text-blue-500"/>
                Лимиты нагуленных профилей
            </h5>

            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <!-- Минимальное количество профилей -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Минимальное количество профилей
                            <span class="text-red-500">*</span>
                        </label>
                        <div class="relative">
                            <input
                                v-model.number="config.min_profiles_limit"
                                type="number"
                                min="1"
                                max="10000"
                                required
                                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 pr-12"
                                placeholder="10"
                            />
                            <div class="absolute inset-y-0 right-0 flex items-center pr-3">
                                <span class="text-gray-500 text-sm">проф.</span>
                            </div>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">
                            Минимальное количество профилей, которые должны быть нагулены
                        </p>
                    </div>

                    <!-- Максимальное количество профилей -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Максимальное количество профилей
                            <span class="text-red-500">*</span>
                        </label>
                        <div class="relative">
                            <input
                                v-model.number="config.max_profiles_limit"
                                type="number"
                                min="1"
                                max="10000"
                                required
                                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 pr-12"
                                placeholder="100"
                            />
                            <div class="absolute inset-y-0 right-0 flex items-center pr-3">
                                <span class="text-gray-500 text-sm">проф.</span>
                            </div>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">
                            Максимальное количество профилей для нагула
                        </p>
                    </div>
                </div>

                <!-- Валидация лимитов -->
                <div v-if="profileLimitsError"
                     class="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                    <div class="flex items-center">
                        <ExclamationTriangleIcon class="h-4 w-4 text-red-500 mr-2"/>
                        <p class="text-sm text-red-600">{{ profileLimitsError }}</p>
                    </div>
                </div>

                <!-- Информационная подсказка -->
                <div class="mt-3 p-3 bg-blue-100 border border-blue-300 rounded-md">
                    <div class="flex items-start">
                        <InformationCircleIcon class="h-4 w-4 text-blue-600 mr-2 mt-0.5"/>
                        <div class="text-sm text-blue-700">
                            <p class="font-medium">Как работают лимиты:</p>
                            <ul class="mt-1 space-y-1 text-xs">
                                <li>• При достижении минимума система продолжает нагул</li>
                                <li>• При достижении максимума нагул приостанавливается</li>
                                <li>• Лимиты помогают контролировать ресурсы и затраты</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Поисковые системы (для search_based и mixed_nurture) -->
        <div v-if="needsSearchEngines">
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Поисковые системы
            </label>
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <div
                    v-for="engine in availableSearchEngines"
                    :key="engine.value"
                    class="flex items-center"
                >
                    <input
                        :id="`engine-${engine.value}`"
                        v-model="config.search_engines"
                        :value="engine.value"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <label
                        :for="`engine-${engine.value}`"
                        class="ml-2 text-sm text-gray-700"
                    >
                        {{ engine.label }}
                    </label>
                </div>
            </div>
        </div>

        <!-- Пропорции (для mixed_nurture) -->
        <div v-if="config.nurture_type === 'mixed_nurture'"
             class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Поисковые заходы (%)
                </label>
                <input
                    v-model.number="config.proportions.search_visits"
                    type="number"
                    min="1"
                    max="99"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    @input="updateDirectVisitsProportions"
                >
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Прямые заходы (%)
                </label>
                <input
                    v-model.number="config.proportions.direct_visits"
                    type="number"
                    min="1"
                    max="99"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    @input="updateSearchVisitsProportions"
                >
            </div>
        </div>

        <!-- Настройки сессии -->
        <div>
            <h4 class="text-sm font-medium text-gray-900 mb-3">Настройки сессии</h4>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Время на сайте (сек)
                    </label>
                    <input
                        v-model.number="config.session_config.timeout_per_site"
                        type="number"
                        min="5"
                        max="120"
                        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Мин. таймаут (сек)
                    </label>
                    <input
                        v-model.number="config.session_config.min_timeout"
                        type="number"
                        min="5"
                        max="60"
                        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Макс. таймаут (сек)
                    </label>
                    <input
                        v-model.number="config.session_config.max_timeout"
                        type="number"
                        min="5"
                        max="120"
                        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                </div>
            </div>
        </div>

        <!-- Источник запросов для поиска -->
        <div v-if="needsQueries">
            <DataSourceImport
                v-model="config.queries_source"
                title="Источник поисковых запросов"
                description="Поисковые запросы для нагула через поисковые системы"
                placeholder="купить телефон&#10;смартфон цена&#10;лучший телефон 2024"
                :allow-refresh="true"
                :strategy-id="strategyId"
                @test="testQueriesSource"
            />
        </div>

        <!-- Источник сайтов для прямых заходов -->
        <div v-if="needsDirectSites">
            <DataSourceImport
                v-model="config.direct_sites_source"
                title="Источник сайтов для прямых заходов"
                description="URL сайтов для прямых переходов"
                placeholder="https://example.com&#10;https://site1.ru&#10;https://site2.com"
                :allow-refresh="true"
                :strategy-id="strategyId"
                @test="testDirectSitesSource"
            />
        </div>

        <!-- Настройки поведения -->
        <div>
            <h4 class="text-sm font-medium text-gray-900 mb-3">Настройки поведения</h4>
            <div class="space-y-3">
                <label class="flex items-center">
                    <input
                        v-model="config.behavior.return_to_search"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <span class="ml-2 text-sm text-gray-700">
                        Возвращаться в поиск после сайта
                    </span>
                </label>

                <label class="flex items-center">
                    <input
                        v-model="config.behavior.close_browser_after_cycle"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <span class="ml-2 text-sm text-gray-700">
                        Закрывать браузер после цикла
                    </span>
                </label>

                <label class="flex items-center">
                    <input
                        v-model="config.behavior.emulate_human_actions"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <span class="ml-2 text-sm text-gray-700">
                        Эмулировать действия человека
                    </span>
                </label>

                <label class="flex items-center">
                    <input
                        v-model="config.behavior.scroll_pages"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <span class="ml-2 text-sm text-gray-700">
                        Прокручивать страницы
                    </span>
                </label>

                <label class="flex items-center">
                    <input
                        v-model="config.behavior.random_clicks"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <span class="ml-2 text-sm text-gray-700">
                        Случайные клики
                    </span>
                </label>
            </div>
        </div>

        <!-- Результаты тестирования -->
        <div v-if="testResults.show" class="rounded-md p-4"
             :class="testResults.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
            <div class="flex">
                <div class="flex-shrink-0">
                    <CheckCircleIcon v-if="testResults.success" class="h-5 w-5 text-green-400"/>
                    <XCircleIcon v-else class="h-5 w-5 text-red-400"/>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium"
                       :class="testResults.success ? 'text-green-800' : 'text-red-800'">
                        {{ testResults.message }}
                    </p>
                    <div v-if="testResults.success && testResults.details"
                         class="mt-2 text-sm text-gray-600">
                        <p>Найдено элементов: {{ testResults.details.count }}</p>
                        <div
                            v-if="testResults.details.samples && testResults.details.samples.length > 0"
                            class="mt-1">
                            <p class="font-medium">Примеры:</p>
                            <ul class="list-disc list-inside">
                                <li v-for="sample in testResults.details.samples" :key="sample">
                                    {{ sample }}
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, computed, watch, onMounted} from 'vue'
import {
    CheckCircleIcon,
    XCircleIcon,
    InformationCircleIcon,
    ExclamationTriangleIcon,
    UsersIcon
} from '@heroicons/vue/24/outline'
import {useStrategiesStore} from '@/stores/strategies'
import DataSourceImport from '@/components/strategies/DataSourceImport.vue'

interface ProfileNurtureConfig {
    nurture_type: string
    target_cookies: {
        min: number
        max: number
    }
    session_config: {
        timeout_per_site: number
        min_timeout: number
        max_timeout: number
    }
    search_engines: string[]
    queries_source: {
        type: string
        source_url?: string
        data_content?: string
        refresh_on_each_cycle: boolean
    }
    behavior: {
        return_to_search: boolean
        close_browser_after_cycle: boolean
        emulate_human_actions: boolean
        scroll_pages: boolean
        random_clicks: boolean
    }
    proportions: {
        search_visits: number
        direct_visits: number
    }
    direct_sites_source?: {
        type: string
        source_url?: string
        data_content?: string
        refresh_on_each_cycle: boolean
    },
    min_profiles_limit: number
    max_profiles_limit: number
}

const props = withDefaults(defineProps<{
    modelValue: ProfileNurtureConfig
    strategyId?: string
}>(), {
    strategyId: undefined
})

const emit = defineEmits<{
    'update:modelValue': [value: ProfileNurtureConfig]
}>()

const strategiesStore = useStrategiesStore()

const config = computed({
    get: () => props.modelValue,
    set: (value: ProfileNurtureConfig) => emit('update:modelValue', value)
})

const availableSearchEngines = ref<Array<{ value: string, label: string }>>([
    {value: 'yandex.ru', label: 'Яндекс (yandex.ru)'},
    {value: 'yandex.by', label: 'Яндекс Беларусь (yandex.by)'},
    {value: 'yandex.kz', label: 'Яндекс Казахстан (yandex.kz)'},
    {value: 'yandex.tr', label: 'Яндекс Турция (yandex.tr)'},
    {value: 'mail.ru', label: 'Mail.ru Поиск'},
    {value: 'dzen.ru', label: 'Дзен Поиск'}
])

const testResults = ref({
    show: false,
    success: false,
    message: '',
    details: null as any
})

const nurtureTypes = [
    {
        value: 'search_based',
        label: 'Через поиск',
        description: 'Поиск в Яндексе + переходы на сайты'
    },
    {
        value: 'direct_visits',
        label: 'Прямые заходы',
        description: 'Прямые переходы на сайты'
    },
    {
        value: 'mixed_nurture',
        label: 'Смешанный',
        description: 'Комбинация поиска и прямых заходов'
    }
]

const needsSearchEngines = computed(() => {
    return ['search_based', 'mixed_nurture'].includes(config.value.nurture_type)
})

const needsQueries = computed(() => {
    return ['search_based', 'mixed_nurture'].includes(config.value.nurture_type)
})

const needsDirectSites = computed(() => {
    return ['direct_visits', 'mixed_nurture'].includes(config.value.nurture_type)
})

const profileLimitsError = computed(() => {
    const min = config.value.min_profiles_limit
    const max = config.value.max_profiles_limit

    if (!min || !max) {
        return 'Укажите минимальное и максимальное количество профилей'
    }

    if (min < 1 || max < 1) {
        return 'Количество профилей должно быть больше 0'
    }

    if (min > max) {
        return 'Минимальное количество не может быть больше максимального'
    }

    if (max > 10000) {
        return 'Максимальное количество не может превышать 10,000'
    }

    return null
})

// Инициализация direct_sites_source если нужно
watch(needsDirectSites, (newValue) => {
    if (newValue && !config.value.direct_sites_source) {
        config.value.direct_sites_source = {
            type: 'manual_input',
            refresh_on_each_cycle: false,
            data_content: ''
        }
    }
}, {immediate: true})

// Обновление пропорций
function updateDirectVisitsProportions() {
    config.value.proportions.direct_visits = 100 - config.value.proportions.search_visits
}

function updateSearchVisitsProportions() {
    config.value.proportions.search_visits = 100 - config.value.proportions.direct_visits
}

// Тестирование источника запросов
async function testQueriesSource(sourceData: any) {
    if (!props.strategyId) return

    testResults.value.show = false

    try {
        const result = await strategiesStore.testQuerySource(props.strategyId, sourceData)

        testResults.value = {
            show: true,
            success: true,
            message: result.message,
            details: {
                count: result.queries_count,
                samples: result.sample_queries
            }
        }
    } catch (error: any) {
        testResults.value = {
            show: true,
            success: false,
            message: error.message || 'Ошибка тестирования источника',
            details: null
        }
    }
}

// Тестирование источника сайтов для прямых заходов
async function testDirectSitesSource(sourceData: any) {
    if (!props.strategyId) return

    testResults.value.show = false

    try {
        const result = await strategiesStore.testQuerySource(props.strategyId, sourceData)

        testResults.value = {
            show: true,
            success: true,
            message: result.message,
            details: {
                count: result.queries_count,
                samples: result.sample_queries
            }
        }
    } catch (error: any) {
        testResults.value = {
            show: true,
            success: false,
            message: error.message || 'Ошибка тестирования источника',
            details: null
        }
    }
}

// Валидация конфигурации
watch(config, async (newConfig) => {
    try {
        await strategiesStore.validateProfileNurtureConfig(newConfig)
    } catch (error) {
        console.warn('Configuration validation failed:', error)
    }
}, {deep: true})
watch([
    () => config.value.min_profiles_limit,
    () => config.value.max_profiles_limit
], () => {
    // Автоисправление: если мин > макс, то макс = мин
    if (config.value.min_profiles_limit > config.value.max_profiles_limit) {
        config.value.max_profiles_limit = config.value.min_profiles_limit
    }
})


onMounted(() => {
    // Инициализация по умолчанию
    if (!config.value.queries_source) {
        config.value.queries_source = {
            type: 'manual_input',
            refresh_on_each_cycle: false,
            data_content: ''
        }
    }
})
</script>
