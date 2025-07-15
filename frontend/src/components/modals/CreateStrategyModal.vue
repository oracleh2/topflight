<!-- frontend/src/components/modals/CreateStrategyModal.vue -->
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
                            class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl sm:p-6">
                            <form @submit.prevent="handleSubmit">
                                <div class="sm:flex sm:items-start">
                                    <div
                                        class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 sm:mx-0 sm:h-10 sm:w-10">
                                        <component
                                            :is="getStrategyIcon()"
                                            class="h-6 w-6 text-primary-600"
                                            aria-hidden="true"
                                        />
                                    </div>
                                    <div
                                        class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
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

                                <div class="mt-6 space-y-6">
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

                                    <!-- Конфигурация стратегии -->
                                    <div>
                                        <h4 class="text-sm font-medium text-gray-900 mb-4">
                                            Конфигурация стратегии
                                        </h4>

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
                                            :strategy-id="temporaryStrategyId"
                                        />
                                    </div>
                                </div>

                                <div class="mt-6 sm:mt-8 sm:flex sm:flex-row-reverse">
                                    <button
                                        type="submit"
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
                            </form>
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
import {BeakerIcon, ChartBarIcon, UserIcon} from '@heroicons/vue/24/outline'
import {useStrategiesStore} from '@/stores/strategies'
import type {StrategyTemplate} from '@/stores/strategies'

// Импортируем компоненты форм
import WarmupForm from '@/components/strategies/WarmupForm.vue'
import PositionCheckForm from '@/components/strategies/PositionCheckForm.vue'
import ProfileNurtureForm from '@/components/strategies/ProfileNurtureForm.vue'

const props = withDefaults(defineProps<{
    isOpen: boolean
    strategyType: 'warmup' | 'position_check' | 'profile_nurture'
}>(), {
    strategyType: 'warmup'
})

const emit = defineEmits<{
    close: []
    created: [strategy: any]
}>()

const strategiesStore = useStrategiesStore()

const templates = ref<StrategyTemplate[]>([])
const loading = ref(false)
const temporaryStrategyId = ref<string | null>(null)

const form = ref({
    template_id: '',
    name: '',
    strategy_type: props.strategyType,
    config: getDefaultConfig()
})

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

// Сбрасываем форму при открытии модального окна
watch(() => props.isOpen, async (isOpen) => {
    if (isOpen) {
        resetForm()
        await loadTemplates()
        // Создаем временную стратегию для тестирования источников данных
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

function resetForm() {
    form.value = {
        template_id: '',
        name: '',
        strategy_type: props.strategyType,
        config: getDefaultConfig()
    }
    temporaryStrategyId.value = null
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

async function handleSubmit() {
    try {
        loading.value = true

        // Валидация для profile_nurture
        if (props.strategyType === 'profile_nurture') {
            const nurtureType = form.value.config.nurture_type

            // Очищаем конфигурацию от ненужных полей
            form.value.config = strategiesStore.cleanProfileNurtureConfig(form.value.config)

            // Валидация источника запросов (обязательно для search_based и mixed_nurture)
            if (['search_based', 'mixed_nurture'].includes(nurtureType)) {
                const queriesErrors = strategiesStore.validateQueriesSource(form.value.config.queries_source)
                if (queriesErrors.length > 0) {
                    throw new Error(`Ошибки в источнике запросов: ${queriesErrors.join(', ')}`)
                }
            }

            // Валидация источника сайтов (обязательно для direct_visits и mixed_nurture)
            if (['direct_visits', 'mixed_nurture'].includes(nurtureType)) {
                if (form.value.config.direct_sites_source) {
                    const sitesErrors = strategiesStore.validateDirectSitesSource(form.value.config.direct_sites_source)
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
            strategy_type: form.value.strategy_type,
            config: form.value.config
        })

        emit('created', strategy)
        resetForm()
    } catch (error) {
        console.error('Error creating strategy:', error)
        // Здесь можно добавить уведомление об ошибке
    } finally {
        loading.value = false
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

// Сбрасываем форму при открытии модального окна
watch(() => props.isOpen, async (isOpen) => {
    if (isOpen) {
        resetForm()
        await loadTemplates()
        // Создаем временную стратегию для тестирования источников данных
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
