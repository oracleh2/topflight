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
                            class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-6xl sm:p-6">
                            <!-- Header -->
                            <div class="sm:flex sm:items-start mb-6">
                                <div
                                    class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 sm:mx-0 sm:h-10 sm:w-10">
                                    <component
                                        :is="getStrategyIcon()"
                                        class="h-6 w-6 text-primary-600"
                                        aria-hidden="true"
                                    />
                                </div>
                                <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                                    <DialogTitle as="h3"
                                                 class="text-base font-semibold leading-6 text-gray-900">
                                        Редактировать стратегию {{ strategyTypeLabel }}
                                    </DialogTitle>
                                    <div class="mt-2">
                                        <p class="text-sm text-gray-500">
                                            Настройте параметры стратегии для
                                            {{ strategyTypeDescription }}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <!-- Tabs Navigation -->
                            <TabsContainer
                                :tabs="tabs"
                                :active-tab="activeTab"
                                @change="activeTab = $event"
                            >
                                <!-- Basic Tab -->
                                <div v-show="activeTab === 'basic'" class="space-y-6">
                                    <h4 class="text-sm font-medium text-gray-900">Основные
                                        настройки</h4>

                                    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                                        <!-- Название стратегии -->
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                Название стратегии
                                            </label>
                                            <input
                                                v-model="form.name"
                                                type="text"
                                                required
                                                maxlength="255"
                                                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                placeholder="Введите название стратегии"
                                            />
                                        </div>

                                        <!-- Статус стратегии -->
                                        <div class="flex items-center">
                                            <label class="flex items-center">
                                                <input
                                                    v-model="form.is_active"
                                                    type="checkbox"
                                                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                                />
                                                <span class="ml-2 text-sm text-gray-700">Активная стратегия</span>
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                <!-- Config Tab -->
                                <div v-show="activeTab === 'config'" class="space-y-6">
                                    <h4 class="text-sm font-medium text-gray-900">Конфигурация
                                        стратегии</h4>

                                    <!-- Warmup Configuration -->
                                    <WarmupForm
                                        v-if="strategy?.strategy_type === 'warmup'"
                                        v-model="form.config"
                                        :is-editing="true"
                                    />

                                    <!-- Position Check Configuration -->
                                    <PositionCheckForm
                                        v-else-if="strategy?.strategy_type === 'position_check'"
                                        v-model="form.config"
                                        :is-editing="true"
                                    />

                                    <!-- Profile Nurture Configuration -->
                                    <ProfileNurtureForm
                                        v-else-if="strategy?.strategy_type === 'profile_nurture'"
                                        v-model="form.config"
                                        :strategy-id="strategy?.id"
                                        :is-editing="true"
                                    />

                                    <!-- Fallback -->
                                    <div v-else class="text-center py-8">
                                        <p class="text-sm text-gray-500">
                                            Неизвестный тип стратегии: {{ strategy?.strategy_type }}
                                        </p>
                                    </div>
                                </div>

                                <!-- Proxy Tab -->
                                <div v-show="activeTab === 'proxy'" class="space-y-6">
                                    <h4 class="text-sm font-medium text-gray-900">Управление
                                        прокси</h4>

                                    <StrategyProxyManager
                                        v-if="strategy?.id"
                                        :strategy-id="strategy.id"
                                    />
                                </div>

                                <!-- Schedule Tab -->
                                <div v-show="activeTab === 'schedule'" class="space-y-6">
                                    <h4 class="text-sm font-medium text-gray-900">Расписание
                                        выполнения</h4>

                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center mb-4">
                                            <ClockIcon class="h-5 w-5 text-blue-500 mr-2"/>
                                            <span class="text-sm font-medium text-gray-700">Автоматическое выполнение</span>
                                        </div>
                                        <p class="text-sm text-gray-600">
                                            Настройки расписания будут реализованы в будущих
                                            версиях.
                                        </p>
                                    </div>
                                </div>
                            </TabsContainer>

                            <!-- Actions -->
                            <div class="mt-8 sm:flex sm:flex-row-reverse">
                                <button
                                    type="button"
                                    @click="handleSubmit"
                                    :disabled="loading || !form.name"
                                    class="inline-flex w-full justify-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:ml-3 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Spinner v-if="loading" class="w-4 h-4 mr-2"/>
                                    {{ loading ? 'Сохранение...' : 'Сохранить изменения' }}
                                </button>
                                <button
                                    type="button"
                                    @click="$emit('close')"
                                    class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                                >
                                    Отмена
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
import {ref, computed, watch} from 'vue'
import {Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot} from '@headlessui/vue'
import {
    PencilIcon,
    BeakerIcon,
    ChartBarIcon,
    UserIcon,
    Cog6ToothIcon,
    GlobeAltIcon,
    ClockIcon
} from '@heroicons/vue/24/outline'
import {useStrategiesStore} from '@/stores/strategies.ts'
import Spinner from '@/components/ui/Spinner.vue'

// Компоненты
import TabsContainer from '@/components/ui/TabsContainer.vue'
import WarmupForm from '@/components/strategies/WarmupForm.vue'
import PositionCheckForm from '@/components/strategies/PositionCheckForm.vue'
import ProfileNurtureForm from '@/components/strategies/ProfileNurtureForm.vue'
import StrategyProxyManager from '@/components/strategies/StrategyProxyManager.vue'

interface Props {
    isOpen: boolean
    strategy: any | null
}

interface WarmupConfig {
    type: string
    proportions: {
        direct_visits: number
        search_visits: number
    }
    min_sites: number
    max_sites: number
    session_timeout: number
    yandex_domain: string
    device_type: string
}

interface PositionCheckConfig {
    check_frequency: string
    yandex_domain: string
    device_type: string
    max_pages: number
    custom_schedule: any
    behavior: {
        random_delays: boolean
        scroll_pages: boolean
        human_like_clicks: boolean
    }
}

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
    queries_source: any
    behavior: {
        return_to_search: boolean
        close_browser_after_cycle: boolean
        emulate_human_actions: boolean
        scroll_pages: boolean
        random_clicks: boolean
    }
    proportions?: {
        search_visits: number
        direct_visits: number
    }
    direct_sites_source?: any
    min_profiles_limit: number
    max_profiles_limit: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
    close: []
    updated: [strategy: any]
}>()

const strategiesStore = useStrategiesStore()
const loading = ref(false)
const activeTab = ref('basic')

const form = ref<{
    name: string
    is_active: boolean
    config: any
}>({
    name: '',
    is_active: true,
    config: {}
})

// Tabs configuration
const tabs = computed(() => [
    {
        id: 'basic',
        label: 'Основные',
        icon: Cog6ToothIcon,
        hasError: !form.value.name
    },
    {
        id: 'config',
        label: 'Конфигурация',
        icon: getStrategyIcon(),
        hasError: false
    },
    {
        id: 'proxy',
        label: 'Прокси',
        icon: GlobeAltIcon,
        hasError: false
    },
    {
        id: 'schedule',
        label: 'Расписание',
        icon: ClockIcon,
        hasError: false
    }
])

const strategyTypeLabel = computed(() => {
    if (!props.strategy) return ''

    switch (props.strategy.strategy_type) {
        case 'warmup':
            return 'прогрева'
        case 'position_check':
            return 'проверки позиций'
        case 'profile_nurture':
            return 'нагула профиля'
        default:
            return props.strategy.strategy_type
    }
})

const strategyTypeDescription = computed(() => {
    if (!props.strategy) return ''

    switch (props.strategy.strategy_type) {
        case 'warmup':
            return 'прогрева сайтов перед проверкой позиций'
        case 'position_check':
            return 'проверки позиций сайтов в поиске'
        case 'profile_nurture':
            return 'нагула профилей браузера для обхода детекции'
        default:
            return ''
    }
})

function getStrategyIcon() {
    if (!props.strategy) return PencilIcon

    switch (props.strategy.strategy_type) {
        case 'warmup':
            return BeakerIcon
        case 'position_check':
            return ChartBarIcon
        case 'profile_nurture':
            return UserIcon
        default:
            return PencilIcon
    }
}

function resetForm() {
    if (props.strategy) {
        form.value = {
            name: props.strategy.name || '',
            is_active: props.strategy.is_active ?? true,
            config: JSON.parse(JSON.stringify(props.strategy.config || {}))
        }
    }
    activeTab.value = 'basic'
}

async function handleSubmit() {
    if (!props.strategy) return

    try {
        loading.value = true

        // Валидация для profile_nurture
        if (props.strategy.strategy_type === 'profile_nurture') {
            const config = form.value.config as ProfileNurtureConfig
            const nurtureType = config.nurture_type

            // Очищаем конфигурацию от ненужных полей
            form.value.config = strategiesStore.cleanProfileNurtureConfig(config)

            // Валидация источника запросов
            if (['search_based', 'mixed_nurture'].includes(nurtureType)) {
                const queriesErrors = strategiesStore.validateQueriesSource(config.queries_source)
                if (queriesErrors.length > 0) {
                    throw new Error(`Ошибки в источнике запросов: ${queriesErrors.join(', ')}`)
                }
            }

            // Валидация источника сайтов
            if (['direct_visits', 'mixed_nurture'].includes(nurtureType)) {
                if (config.direct_sites_source) {
                    const sitesErrors = strategiesStore.validateDirectSitesSource(config.direct_sites_source)
                    if (sitesErrors.length > 0) {
                        throw new Error(`Ошибки в источнике сайтов: ${sitesErrors.join(', ')}`)
                    }
                } else {
                    throw new Error('Источник сайтов обязателен для прямых заходов')
                }
            }
        }

        const strategy = await strategiesStore.updateStrategy(props.strategy.id, {
            name: form.value.name,
            is_active: form.value.is_active,
            config: form.value.config
        })

        emit('updated', strategy)
    } catch (error) {
        console.error('Error updating strategy:', error)
        const errorMessage = error instanceof Error ? error.message : 'Неизвестная ошибка'
        alert(`Ошибка при сохранении стратегии: ${errorMessage}`)
    } finally {
        loading.value = false
    }
}

// Заполняем форму при открытии модального окна или изменении стратегии
watch([() => props.isOpen, () => props.strategy], ([isOpen, strategy]) => {
    if (isOpen && strategy) {
        resetForm()
    }
}, {immediate: true})
</script>
