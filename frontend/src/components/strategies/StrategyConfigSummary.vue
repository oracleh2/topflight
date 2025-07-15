<!-- frontend/src/components/StrategyConfigSummary.vue -->
<template>
    <div class="bg-gray-50 rounded-lg p-4 space-y-3">
        <h5 class="text-sm font-medium text-gray-900">Конфигурация стратегии</h5>

        <!-- Warmup Strategy Summary -->
        <div v-if="strategy.strategy_type === 'warmup'" class="space-y-2">
            <div class="flex justify-between text-sm">
                <span class="text-gray-600">Тип стратегии:</span>
                <span class="font-medium">{{ getWarmupTypeLabel(strategy.config.type) }}</span>
            </div>
            <div v-if="strategy.config.type === 'mixed'" class="flex justify-between text-sm">
                <span class="text-gray-600">Пропорции:</span>
                <span class="font-medium">
                    {{
                        strategy.config.proportions?.direct_visits || 5
                    }}:{{ strategy.config.proportions?.search_visits || 1 }}
                    (прямые:поиск)
                </span>
            </div>
            <div v-if="strategy.config.search_config?.yandex_domains"
                 class="flex justify-between text-sm">
                <span class="text-gray-600">Домены Яндекса:</span>
                <span class="font-medium">{{
                        strategy.config.search_config.yandex_domains.join(', ')
                    }}</span>
            </div>
        </div>

        <!-- Position Check Strategy Summary -->
        <div v-else-if="strategy.strategy_type === 'position_check'" class="space-y-2">
            <div class="flex justify-between text-sm">
                <span class="text-gray-600">Частота проверки:</span>
                <span class="font-medium">{{
                        getCheckFrequencyLabel(strategy.config.check_frequency)
                    }}</span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-600">Страниц для проверки:</span>
                <span class="font-medium">{{
                        strategy.config.search_config?.pages_to_check || 10
                    }}</span>
            </div>
            <div v-if="strategy.config.search_config?.device_types"
                 class="flex justify-between text-sm">
                <span class="text-gray-600">Типы устройств:</span>
                <span class="font-medium">{{
                        getDeviceTypesLabel(strategy.config.search_config.device_types)
                    }}</span>
            </div>
        </div>

        <!-- Profile Nurture Strategy Summary -->
        <div v-else-if="strategy.strategy_type === 'profile_nurture'" class="space-y-2">
            <div class="flex justify-between text-sm">
                <span class="text-gray-600">Тип нагула:</span>
                <span class="font-medium">{{
                        getNurtureTypeLabel(strategy.config.nurture_type)
                    }}</span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-600">Целевые куки:</span>
                <span class="font-medium">
                    {{
                        strategy.config.target_cookies?.min || 50
                    }}-{{ strategy.config.target_cookies?.max || 100 }}
                </span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-600">Время на сайте:</span>
                <span class="font-medium">{{
                        strategy.config.session_config?.timeout_per_site || 15
                    }} сек</span>
            </div>
            <div v-if="strategy.config.search_engines?.length" class="flex justify-between text-sm">
                <span class="text-gray-600">Поисковые системы:</span>
                <span class="font-medium">{{ strategy.config.search_engines.join(', ') }}</span>
            </div>
            <div v-if="strategy.config.proportions" class="flex justify-between text-sm">
                <span class="text-gray-600">Пропорции:</span>
                <span class="font-medium">
                    {{
                        strategy.config.proportions.search_visits
                    }}:{{ strategy.config.proportions.direct_visits }}
                    (поиск:прямые)
                </span>
            </div>

            <!-- Источники данных для нагула -->
            <div class="border-t pt-2 mt-2">
                <div
                    v-if="strategy.config.queries_source?.data_content || strategy.config.queries_source?.source_url"
                    class="flex justify-between text-sm">
                    <span class="text-gray-600">Источник запросов:</span>
                    <span class="font-medium">{{
                            getSourceTypeLabel(strategy.config.queries_source.type)
                        }}</span>
                </div>
                <div v-if="strategy.config.queries_source?.data_content"
                     class="flex justify-between text-sm">
                    <span class="text-gray-600">Запросов:</span>
                    <span class="font-medium">{{
                            getQueriesCount(strategy.config.queries_source.data_content)
                        }}</span>
                </div>
                <div
                    v-if="strategy.config.direct_sites_source?.data_content || strategy.config.direct_sites_source?.source_url"
                    class="flex justify-between text-sm">
                    <span class="text-gray-600">Источник сайтов:</span>
                    <span class="font-medium">{{
                            getSourceTypeLabel(strategy.config.direct_sites_source.type)
                        }}</span>
                </div>
                <div v-if="strategy.config.direct_sites_source?.data_content"
                     class="flex justify-between text-sm">
                    <span class="text-gray-600">Сайтов:</span>
                    <span class="font-medium">{{
                            getQueriesCount(strategy.config.direct_sites_source.data_content)
                        }}</span>
                </div>
            </div>
        </div>

        <!-- Status -->
        <div class="flex justify-between text-sm pt-2 border-t">
            <span class="text-gray-600">Статус:</span>
            <span :class="[
                'font-medium',
                strategy.is_active ? 'text-green-600' : 'text-gray-400'
            ]">
                {{ strategy.is_active ? 'Активна' : 'Неактивна' }}
            </span>
        </div>

        <!-- Last Updated -->
        <div class="flex justify-between text-sm">
            <span class="text-gray-600">Обновлена:</span>
            <span class="font-medium">{{ formatDate(strategy.updated_at) }}</span>
        </div>

        <!-- Edit Button -->
        <div class="pt-2 border-t">
            <button
                @click="$emit('edit')"
                class="w-full text-sm text-primary-600 hover:text-primary-500 font-medium"
            >
                Изменить
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
interface Props {
    strategy: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
    edit: []
}>()

function getWarmupTypeLabel(type: string): string {
    switch (type) {
        case 'direct':
            return 'Прямые заходы'
        case 'search':
            return 'Только поиск'
        case 'mixed':
            return 'Смешанный'
        default:
            return type
    }
}

function getCheckFrequencyLabel(frequency: string): string {
    switch (frequency) {
        case 'daily':
            return 'Ежедневно'
        case 'weekly':
            return 'Еженедельно'
        case 'monthly':
            return 'Ежемесячно'
        case 'custom':
            return 'Пользовательское'
        default:
            return frequency
    }
}

function getDeviceTypesLabel(devices: string[]): string {
    if (!devices || devices.length === 0) return 'Не указано'

    const labels = devices.map(device => {
        switch (device) {
            case 'desktop':
                return 'Десктоп'
            case 'mobile':
                return 'Мобильное'
            default:
                return device
        }
    })

    return labels.join(', ')
}

function getNurtureTypeLabel(type: string): string {
    switch (type) {
        case 'search_based':
            return 'Через поиск'
        case 'direct_visits':
            return 'Прямые заходы'
        case 'mixed_nurture':
            return 'Смешанный'
        default:
            return type
    }
}

function getSourceTypeLabel(type: string): string {
    switch (type) {
        case 'manual_input':
            return 'Ручной ввод'
        case 'file_upload':
            return 'Загрузка файла'
        case 'url_import':
            return 'Импорт по URL'
        case 'url_endpoint':
            return 'URL эндпоинт'
        case 'google_sheets':
            return 'Google Таблицы'
        case 'google_docs':
            return 'Google Документы'
        default:
            return type
    }
}

function getQueriesCount(content: string): number {
    if (!content) return 0
    return content.split('\n').filter(line => line.trim()).length
}

function formatDate(dateString: string): string {
    if (!dateString) return 'Не указано'

    const date = new Date(dateString)
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}
</script>
