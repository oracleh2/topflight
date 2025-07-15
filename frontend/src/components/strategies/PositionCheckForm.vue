<!-- frontend/src/components/strategies/PositionCheckForm.vue -->
<template>
    <div class="space-y-6">
        <!-- Частота проверки -->
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Частота проверки
            </label>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div
                    v-for="frequency in checkFrequencies"
                    :key="frequency.value"
                    class="relative"
                >
                    <input
                        :id="`frequency-${frequency.value}`"
                        v-model="config.check_frequency"
                        :value="frequency.value"
                        type="radio"
                        class="sr-only peer"
                    >
                    <label
                        :for="`frequency-${frequency.value}`"
                        class="flex items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-900 hover:bg-gray-50 peer-checked:border-primary-600 peer-checked:bg-primary-50 peer-checked:text-primary-600 cursor-pointer"
                    >
                        <div class="text-center">
                            <div class="font-medium">{{ frequency.label }}</div>
                            <div class="text-xs text-gray-500 mt-1">{{
                                    frequency.description
                                }}
                            </div>
                        </div>
                    </label>
                </div>
            </div>
        </div>

        <!-- Пользовательское расписание (для custom) -->
        <div v-if="config.check_frequency === 'custom'">
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Расписание (cron выражение)
            </label>
            <input
                v-model="config.custom_schedule"
                type="text"
                placeholder="0 9 * * *"
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 font-mono"
            >
            <p class="mt-1 text-xs text-gray-500">
                Введите cron выражение для настройки расписания. Например: "0 9 * * *" для
                ежедневной проверки в 9:00
            </p>
        </div>

        <!-- Максимальное количество страниц -->
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Максимальное количество страниц для проверки
            </label>
            <input
                v-model.number="config.max_pages"
                type="number"
                min="1"
                max="50"
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
            <p class="mt-1 text-xs text-gray-500">
                Максимальное количество страниц поиска для анализа позиций
            </p>
        </div>

        <!-- Домен Яндекса -->
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Домен Яндекса
            </label>
            <select
                v-model="config.yandex_domain"
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
                <option value="yandex.ru">yandex.ru (Россия)</option>
                <option value="yandex.by">yandex.by (Беларусь)</option>
                <option value="yandex.kz">yandex.kz (Казахстан)</option>
                <option value="yandex.ua">yandex.ua (Украина)</option>
            </select>
        </div>

        <!-- Тип устройства -->
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Тип устройства
            </label>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div class="relative">
                    <input
                        id="device-desktop-check"
                        v-model="config.device_type"
                        value="desktop"
                        type="radio"
                        class="sr-only peer"
                    >
                    <label
                        for="device-desktop-check"
                        class="flex items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-900 hover:bg-gray-50 peer-checked:border-primary-600 peer-checked:bg-primary-50 peer-checked:text-primary-600 cursor-pointer"
                    >
                        Десктоп
                    </label>
                </div>
                <div class="relative">
                    <input
                        id="device-mobile-check"
                        v-model="config.device_type"
                        value="mobile"
                        type="radio"
                        class="sr-only peer"
                    >
                    <label
                        for="device-mobile-check"
                        class="flex items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-900 hover:bg-gray-50 peer-checked:border-primary-600 peer-checked:bg-primary-50 peer-checked:text-primary-600 cursor-pointer"
                    >
                        Мобильный
                    </label>
                </div>
            </div>
        </div>

        <!-- Настройки поведения -->
        <div>
            <h4 class="text-sm font-medium text-gray-900 mb-3">Настройки поведения</h4>
            <div class="space-y-3">
                <label class="flex items-center">
                    <input
                        v-model="config.behavior.random_delays"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <span class="ml-2 text-sm text-gray-700">
                        Случайные задержки между действиями
                    </span>
                </label>

                <label class="flex items-center">
                    <input
                        v-model="config.behavior.scroll_pages"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <span class="ml-2 text-sm text-gray-700">
                        Прокручивать страницы результатов
                    </span>
                </label>

                <label class="flex items-center">
                    <input
                        v-model="config.behavior.human_like_clicks"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                    <span class="ml-2 text-sm text-gray-700">
                        Имитировать клики пользователя
                    </span>
                </label>
            </div>
        </div>

        <!-- Дополнительные настройки поиска -->
        <div>
            <h4 class="text-sm font-medium text-gray-900 mb-3">Дополнительные настройки</h4>
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Регион поиска
                    </label>
                    <select
                        v-model="config.search_config.region"
                        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                        <option value="">Автоматически</option>
                        <option value="moscow">Москва</option>
                        <option value="spb">Санкт-Петербург</option>
                        <option value="ekaterinburg">Екатеринбург</option>
                        <option value="novosibirsk">Новосибирск</option>
                        <option value="kazan">Казань</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Язык интерфейса
                    </label>
                    <select
                        v-model="config.search_config.language"
                        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                        <option value="ru">Русский</option>
                        <option value="en">English</option>
                        <option value="uk">Українська</option>
                        <option value="be">Беларуская</option>
                        <option value="kk">Қазақша</option>
                    </select>
                </div>

                <div>
                    <label class="flex items-center">
                        <input
                            v-model="config.search_config.safe_search"
                            type="checkbox"
                            class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        >
                        <span class="ml-2 text-sm text-gray-700">
                            Безопасный поиск
                        </span>
                    </label>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {computed, watch} from 'vue'

interface PositionCheckConfig {
    check_frequency: string
    custom_schedule?: string
    max_pages: number
    yandex_domain: string
    device_type: string
    behavior: {
        random_delays: boolean
        scroll_pages: boolean
        human_like_clicks: boolean
    }
    search_config: {
        region?: string
        language: string
        safe_search: boolean
    }
}

const props = withDefaults(defineProps<{
    modelValue: PositionCheckConfig
}>(), {})

const emit = defineEmits<{
    'update:modelValue': [value: PositionCheckConfig]
}>()

const config = computed({
    get: () => props.modelValue,
    set: (value: PositionCheckConfig) => emit('update:modelValue', value)
})

const checkFrequencies = [
    {
        value: 'daily',
        label: 'Ежедневно',
        description: 'Каждый день'
    },
    {
        value: 'weekly',
        label: 'Еженедельно',
        description: 'Раз в неделю'
    },
    {
        value: 'monthly',
        label: 'Ежемесячно',
        description: 'Раз в месяц'
    },
    {
        value: 'custom',
        label: 'Настраиваемо',
        description: 'Cron расписание'
    }
]

// Инициализация значений по умолчанию
watch(() => props.modelValue, (newValue) => {
    if (!newValue.behavior) {
        config.value.behavior = {
            random_delays: true,
            scroll_pages: true,
            human_like_clicks: true
        }
    }

    if (!newValue.search_config) {
        config.value.search_config = {
            language: 'ru',
            safe_search: false
        }
    }
}, {immediate: true, deep: true})

// Очистка custom_schedule при изменении частоты
watch(() => config.value.check_frequency, (newFreq) => {
    if (newFreq !== 'custom') {
        config.value.custom_schedule = undefined
    }
})
</script>
