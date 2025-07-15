<!-- frontend/src/components/StrategyConfigSummary.vue -->
<template>
    <div class="bg-gray-50 rounded-lg p-4">
        <div class="flex items-center justify-between mb-3">
            <h4 class="text-sm font-medium text-gray-900">Конфигурация стратегии</h4>
            <button
                @click="$emit('edit')"
                class="text-xs text-primary-600 hover:text-primary-500 font-medium"
            >
                Изменить
            </button>
        </div>

        <!-- Стратегия прогрева -->
        <div v-if="strategy.strategy_type === 'warmup'" class="space-y-2">
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Тип стратегии:</span>
                <span class="text-sm font-medium text-gray-900">
                    {{ getWarmupTypeLabel(strategy.config.type) }}
                </span>
            </div>

            <!-- Пропорции для mixed стратегии -->
            <div v-if="strategy.config.type === 'mixed'" class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Пропорции:</span>
                <span class="text-sm font-medium text-gray-900">
                    {{
                        strategy.config.proportions?.direct_visits || 5
                    }}:{{ strategy.config.proportions?.search_visits || 1 }}
                    <span class="text-xs text-gray-500">(прямые:поиск)</span>
                </span>
            </div>

            <!-- Домены Яндекса -->
            <div v-if="strategy.config.type === 'search' || strategy.config.type === 'mixed'">
                <div class="flex justify-between items-start">
                    <span class="text-sm text-gray-600">Домены Яндекса:</span>
                    <div class="text-right">
                        <div class="text-sm font-medium text-gray-900">
                            {{
                                getYandexDomainsText(strategy.config.search_config?.yandex_domains)
                            }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Дополнительные настройки -->
            <div v-if="strategy.config.direct_config" class="pt-2 border-t border-gray-200">
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600">Время на сайте:</span>
                    <span class="text-sm font-medium text-gray-900">
                        {{
                            strategy.config.direct_config.time_per_site?.min || 10
                        }}-{{ strategy.config.direct_config.time_per_site?.max || 45 }} мин
                    </span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600">Сайтов за сессию:</span>
                    <span class="text-sm font-medium text-gray-900">
                        {{
                            strategy.config.direct_config.sites_per_session?.min || 3
                        }}-{{ strategy.config.direct_config.sites_per_session?.max || 7 }}
                    </span>
                </div>
            </div>
        </div>

        <!-- Стратегия проверки позиций -->
        <div v-if="strategy.strategy_type === 'position_check'" class="space-y-2">
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Частота проверки:</span>
                <span class="text-sm font-medium text-gray-900">
                    {{ getCheckFrequencyLabel(strategy.config.check_frequency) }}
                </span>
            </div>

            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Страниц для проверки:</span>
                <span class="text-sm font-medium text-gray-900">
                    {{ strategy.config.search_config?.pages_to_check || 10 }}
                </span>
            </div>

            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Устройства:</span>
                <span class="text-sm font-medium text-gray-900">
                    {{ getDeviceTypesText(strategy.config.search_config?.device_types) }}
                </span>
            </div>

            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600">Домен Яндекса:</span>
                <span class="text-sm font-medium text-gray-900">
                    {{ strategy.config.search_config?.yandex_domain || 'yandex.ru' }}
                </span>
            </div>

            <!-- Поведенческие настройки -->
            <div v-if="strategy.config.behavior" class="pt-2 border-t border-gray-200">
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600">Время на SERP:</span>
                    <span class="text-sm font-medium text-gray-900">
                        {{
                            strategy.config.behavior.time_on_serp?.min || 5
                        }}-{{ strategy.config.behavior.time_on_serp?.max || 15 }} сек
                    </span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600">Прокрутка SERP:</span>
                    <span class="text-sm font-medium text-gray-900">
                        {{ strategy.config.behavior.scroll_serp ? 'Да' : 'Нет' }}
                    </span>
                </div>
            </div>
        </div>

        <!-- Статус активности -->
        <div class="flex justify-between items-center mt-3 pt-3 border-t border-gray-200">
            <span class="text-sm text-gray-600">Статус:</span>
            <span :class="[
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                strategy.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
            ]">
                {{ strategy.is_active ? 'Активна' : 'Неактивна' }}
            </span>
        </div>

        <!-- Последнее обновление -->
        <div class="flex justify-between items-center mt-1">
            <span class="text-sm text-gray-600">Обновлена:</span>
            <span class="text-xs text-gray-500">
                {{ formatDate(strategy.updated_at) }}
            </span>
        </div>
    </div>
</template>

<script setup lang="ts">
interface Props {
    strategy: any
}

interface Emits {
    (e: 'edit'): void
}

defineProps<Props>()
defineEmits<Emits>()

function getWarmupTypeLabel(type: string): string {
    const labels = {
        'direct': 'Только прямые заходы',
        'search': 'Только поиск в Яндексе',
        'mixed': 'Комбинированная стратегия'
    }
    return labels[type] || type
}

function getCheckFrequencyLabel(frequency: string): string {
    const labels = {
        'daily': 'Ежедневно',
        'weekly': 'Еженедельно',
        'monthly': 'Ежемесячно',
        'custom': 'Пользовательское'
    }
    return labels[frequency] || frequency
}

function getYandexDomainsText(domains: string[]): string {
    if (!domains || domains.length === 0) return 'yandex.ru'
    if (domains.length === 1) return domains[0]
    if (domains.length <= 3) return domains.join(', ')
    return `${domains.slice(0, 2).join(', ')} и еще ${domains.length - 2}`
}

function getDeviceTypesText(devices: string[]): string {
    if (!devices || devices.length === 0) return 'Десктоп'

    const labels = {
        'desktop': 'Десктоп',
        'mobile': 'Мобильное'
    }

    return devices.map(device => labels[device] || device).join(', ')
}

function formatDate(dateString: string): string {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date)
}
</script>
