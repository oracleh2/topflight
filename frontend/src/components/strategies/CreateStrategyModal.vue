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
                                        Создать стратегию {{ getStrategyTypeLabel() }}
                                    </DialogTitle>
                                    <div class="mt-2">
                                        <p class="text-sm text-gray-500">
                                            Создайте новую стратегию для
                                            {{ getStrategyTypeDescription() }}
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

                                    <!-- Выбор шаблона -->
                                    <div v-if="templates.length > 0">
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Выберите шаблон (опционально)
                                        </label>
                                        <select
                                            v-model="form.template_id"
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            @change="handleTemplateChange"
                                        >
                                            <option value="">Создать с нуля</option>
                                            <option
                                                v-for="template in templates"
                                                :key="template.id"
                                                :value="template.id"
                                            >
                                                {{ template.name }}
                                                <span v-if="template.is_system"
                                                      class="text-gray-500">(системный)</span>
                                            </option>
                                        </select>
                                        <p class="mt-1 text-xs text-gray-500">
                                            Выберите готовый шаблон или создайте стратегию с нуля
                                        </p>
                                    </div>

                                    <!-- Название стратегии -->
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Название стратегии
                                        </label>
                                        <input
                                            v-model="form.name"
                                            type="text"
                                            required
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            :placeholder="`Моя стратегия ${getStrategyTypeLabel().toLowerCase()}`"
                                        >
                                    </div>

                                    <!-- Статус -->
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

                                <!-- Config Tab -->
                                <div v-show="activeTab === 'config'" class="space-y-6">
                                    <h4 class="text-sm font-medium text-gray-900">Конфигурация
                                        стратегии</h4>

                                    <!-- Warmup Configuration -->
                                    <WarmupForm
                                        v-if="strategyType === 'warmup'"
                                        v-model="form.config"
                                    />

                                    <!-- Position Check Configuration -->
                                    <PositionCheckForm
                                        v-else-if="strategyType === 'position_check'"
                                        v-model="form.config"
                                    />

                                    <!-- Profile Nurture Configuration -->
                                    <ProfileNurtureForm
                                        v-else-if="strategyType === 'profile_nurture'"
                                        v-model="form.config"
                                        :strategy-id="temporaryStrategyId || undefined"
                                    />
                                </div>

                                <!-- Proxy Tab -->
                                <div v-show="activeTab === 'proxy'" class="space-y-6">
                                    <h4 class="text-sm font-medium text-gray-900">Управление
                                        прокси</h4>

                                    <div class="bg-gray-50 rounded-lg p-4">
                                        <div class="flex items-center mb-4">
                                            <ExclamationCircleIcon
                                                class="h-5 w-5 text-amber-500 mr-2"/>
                                            <span class="text-sm font-medium text-gray-700">Настройка прокси</span>
                                        </div>
                                        <p class="text-sm text-gray-600">
                                            Прокси можно будет настроить после создания стратегии в
                                            режиме редактирования.
                                        </p>
                                    </div>
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
                                            Настройки расписания будут доступны после создания
                                            стратегии.
                                        </p>
                                    </div>
                                </div>
                            </TabsContainer>

                            <!-- Actions -->
                            <div class="mt-8 sm:flex sm:flex-row-reverse">
                                <button
                                    type="button"
                                    @click="handleSubmit"
                                    :disabled="loading"
                                    class="inline-flex w-full justify-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:ml-3 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {{ loading ? 'Создание...' : 'Создать стратегию' }}
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
import {ref, computed, watch, onMounted} from 'vue'
import {Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot} from '@headlessui/vue'
import {
    BeakerIcon,
    ChartBarIcon,
    UserIcon,
    Cog6ToothIcon,
    GlobeAltIcon,
    ClockIcon,
    ExclamationCircleIcon
} from '@heroicons/vue/24/outline'
import {useStrategiesStore} from '@/stores/strategies.ts'
import type {StrategyTemplate} from '@/stores/strategies.ts'

// Компоненты
import TabsContainer from '@/components/ui/TabsContainer.vue'
import WarmupForm from '@/components/strategies/WarmupForm.vue'
import PositionCheckForm from '@/components/strategies/PositionCheckForm.vue'
import ProfileNurtureForm from '@/components/strategies/ProfileNurtureForm.vue'

const props = withDefaults(defineProps<{
    isOpen: boolean
    strategyType: 'warmup' | 'position_check' | 'profile_nurture'
}>(), {
    strategyType: 'warmup'
})

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
}

const emit = defineEmits<{
    close: []
    created: [strategy: any]
}>()

const strategiesStore = useStrategiesStore()

// Reactive data
const templates = ref<StrategyTemplate[]>([])
const loading = ref(false)
const temporaryStrategyId = ref<string | null>(null)
const activeTab = ref('basic')

const form = ref<{
    template_id: string
    name: string
    strategy_type: string
    is_active: boolean
    config: any
}>({
    template_id: '',
    name: '',
    strategy_type: props.strategyType,
    is_active: true,
    config: getDefaultConfig()
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

function getDefaultConfig() {
    switch (props.strategyType) {
        case 'warmup':
            return strategiesStore.getDefaultWarmupConfig()
        case 'position_check':
            return strategiesStore.getDefaultPositionCheckConfig()
        case 'profile_nurture':
            return strategiesStore.getEnhancedProfileNurtureConfig()
        default:
            return {}
    }
}

function getStrategyIcon() {
    switch (props.strategyType) {
        case 'warmup':
            return BeakerIcon
        case 'position_check':
            return ChartBarIcon
        case 'profile_nurture':
            return UserIcon
        default:
            return BeakerIcon
    }
}

function getStrategyTypeLabel(): string {
    switch (props.strategyType) {
        case 'warmup':
            return 'прогрева'
        case 'position_check':
            return 'проверки позиций'
        case 'profile_nurture':
            return 'нагула профиля'
        default:
            return props.strategyType
    }
}

function getStrategyTypeDescription(): string {
    switch (props.strategyType) {
        case 'warmup':
            return 'прогрева сайтов перед проверкой позиций'
        case 'position_check':
            return 'проверки позиций сайтов в поиске'
        case 'profile_nurture':
            return 'нагула профилей браузера для обхода детекции'
        default:
            return ''
    }
}

function getTemplatesByType() {
    switch (props.strategyType) {
        case 'warmup':
            return strategiesStore.warmupTemplates
        case 'position_check':
            return strategiesStore.positionCheckTemplates
        case 'profile_nurture':
            return strategiesStore.profileNurtureTemplates
        default:
            return []
    }
}

function resetForm() {
    form.value = {
        template_id: '',
        name: '',
        strategy_type: props.strategyType,
        is_active: true,
        config: getDefaultConfig()
    }
    temporaryStrategyId.value = null
    activeTab.value = 'basic'
}

function handleTemplateChange() {
    if (form.value.template_id) {
        const template = templates.value.find(t => t.id === form.value.template_id)
        if (template) {
            form.value.name = `${template.name} (копия)`
            form.value.config = {...template.config}
        }
    } else {
        form.value.config = getDefaultConfig()
    }
}

async function createTemporaryStrategy() {
    try {
        if (props.strategyType === 'profile_nurture') {
            const tempStrategy = await strategiesStore.createTemporaryStrategy({
                name: form.value.name || `Временная стратегия ${Date.now()}`,
                strategy_type: form.value.strategy_type,
                config: form.value.config
            })
            temporaryStrategyId.value = tempStrategy.id
        }
    } catch (error) {
        console.error('Error creating temporary strategy:', error)
    }
}

async function loadTemplates() {
    try {
        await strategiesStore.fetchStrategyTemplates(props.strategyType)
        templates.value = getTemplatesByType()
    } catch (error) {
        console.error('Error loading templates:', error)
    }
}

async function handleSubmit() {
    try {
        loading.value = true

        // Валидация для profile_nurture
        if (props.strategyType === 'profile_nurture') {
            const config = form.value.config as any
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

        const strategy = await strategiesStore.createStrategy({
            template_id: form.value.template_id || undefined,
            name: form.value.name,
            strategy_type: form.value.strategy_type as 'warmup' | 'position_check' | 'profile_nurture',
            config: form.value.config
        })

        emit('created', strategy)
        resetForm()
    } catch (error) {
        console.error('Error creating strategy:', error)
        const errorMessage = error instanceof Error ? error.message : 'Неизвестная ошибка'
        alert(`Ошибка при создании стратегии: ${errorMessage}`)
    } finally {
        loading.value = false
    }
}

// Сбрасываем форму при открытии модального окна
watch(() => props.isOpen, async (isOpen) => {
    if (isOpen) {
        resetForm()
        await loadTemplates()
        if (props.strategyType === 'profile_nurture') {
            await createTemporaryStrategy()
        }
    }
})

// Обновляем тип стратегии при изменении props
watch(() => props.strategyType, async (newType) => {
    form.value.strategy_type = newType
    form.value.config = getDefaultConfig()
    await loadTemplates()
    if (newType === 'profile_nurture') {
        await createTemporaryStrategy()
    }
})

// Загружаем шаблоны при монтировании
onMounted(async () => {
    if (props.isOpen) {
        await loadTemplates()
        if (props.strategyType === 'profile_nurture') {
            await createTemporaryStrategy()
        }
    }
})
</script>
