<!-- frontend/src/components/strategies/WarmupForm.vue -->
<template>
    <div class="space-y-6">
        <!-- Тип прогрева -->
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Тип прогрева
            </label>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div
                    v-for="type in warmupTypes"
                    :key="type.value"
                    class="relative"
                >
                    <input
                        :id="`warmup-type-${type.value}`"
                        v-model="config.type"
                        :value="type.value"
                        type="radio"
                        class="sr-only peer"
                    >
                    <label
                        :for="`warmup-type-${type.value}`"
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

        <!-- Пропорции (для смешанного типа) -->
        <div v-if="config.type === 'mixed'" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
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

        <!-- Количество сайтов -->
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Минимум сайтов
                </label>
                <input
                    v-model.number="config.min_sites"
                    type="number"
                    min="1"
                    max="20"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Максимум сайтов
                </label>
                <input
                    v-model.number="config.max_sites"
                    type="number"
                    min="1"
                    max="20"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
            </div>
        </div>

        <!-- Таймаут сессии -->
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Таймаут сессии (секунды)
            </label>
            <input
                v-model.number="config.session_timeout"
                type="number"
                min="5"
                max="120"
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
            <p class="mt-1 text-xs text-gray-500">
                Время, которое тратится на каждом сайте
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
                        id="device-desktop"
                        v-model="config.device_type"
                        value="desktop"
                        type="radio"
                        class="sr-only peer"
                    >
                    <label
                        for="device-desktop"
                        class="flex items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-900 hover:bg-gray-50 peer-checked:border-primary-600 peer-checked:bg-primary-50 peer-checked:text-primary-600 cursor-pointer"
                    >
                        Десктоп
                    </label>
                </div>
                <div class="relative">
                    <input
                        id="device-mobile"
                        v-model="config.device_type"
                        value="mobile"
                        type="radio"
                        class="sr-only peer"
                    >
                    <label
                        for="device-mobile"
                        class="flex items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-900 hover:bg-gray-50 peer-checked:border-primary-600 peer-checked:bg-primary-50 peer-checked:text-primary-600 cursor-pointer"
                    >
                        Мобильный
                    </label>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {computed} from 'vue'

interface WarmupConfig {
    type: string
    proportions: {
        search_visits: number
        direct_visits: number
    }
    min_sites: number
    max_sites: number
    session_timeout: number
    yandex_domain: string
    device_type: string
}

const props = withDefaults(defineProps<{
    modelValue: WarmupConfig
}>(), {})

const emit = defineEmits<{
    'update:modelValue': [value: WarmupConfig]
}>()

const config = computed({
    get: () => props.modelValue,
    set: (value: WarmupConfig) => emit('update:modelValue', value)
})

const warmupTypes = [
    {
        value: 'direct',
        label: 'Прямые заходы',
        description: 'Только прямые переходы на сайты'
    },
    {
        value: 'search',
        label: 'Только поиск',
        description: 'Только поиск в Яндексе'
    },
    {
        value: 'mixed',
        label: 'Смешанный',
        description: 'Комбинация поиска и прямых заходов'
    }
]

// Обновление пропорций
function updateDirectVisitsProportions() {
    config.value.proportions.direct_visits = 100 - config.value.proportions.search_visits
}

function updateSearchVisitsProportions() {
    config.value.proportions.search_visits = 100 - config.value.proportions.direct_visits
}
</script>
