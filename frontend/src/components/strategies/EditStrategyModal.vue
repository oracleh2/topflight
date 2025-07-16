<!-- frontend/src/components/modals/EditStrategyModal.vue -->
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

                                <div class="mt-6 space-y-6">
                                    <!-- Основные настройки -->
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

                                    <!-- Конфигурация стратегии -->
                                    <div>
                                        <h4 class="text-sm font-medium text-gray-900 mb-4">
                                            Конфигурация стратегии
                                        </h4>

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

                                        <!-- Fallback for unknown strategy types -->
                                        <div v-else class="text-center py-8">
                                            <p class="text-sm text-gray-500">
                                                Неизвестный тип стратегии:
                                                {{ strategy?.strategy_type }}
                                            </p>
                                        </div>
                                    </div>
                                    <!-- Управление прокси -->
                                    <div>
                                        <h4 class="text-sm font-medium text-gray-900 mb-4">
                                            Управление прокси
                                        </h4>

                                        <StrategyProxyManager
                                            v-if="strategy?.id"
                                            :strategy-id="strategy.id"
                                        />
                                    </div>
                                </div>

                                <div class="mt-6 sm:mt-8 sm:flex sm:flex-row-reverse">
                                    <button
                                        type="submit"
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
                            </form>
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
import {PencilIcon, BeakerIcon, ChartBarIcon, UserIcon} from '@heroicons/vue/24/outline'
import {useStrategiesStore} from '@/stores/strategies.ts'
import Spinner from '@/components/ui/Spinner.vue'

// Импортируем компоненты форм
import WarmupForm from '@/components/strategies/WarmupForm.vue'
import PositionCheckForm from '@/components/strategies/PositionCheckForm.vue'
import ProfileNurtureForm from '@/components/strategies/ProfileNurtureForm.vue'
import StrategyProxyManager from '@/components/strategies/StrategyProxyManager.vue'

interface Props {
    isOpen: boolean
    strategy: any | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
    close: []
    updated: [strategy: any]
}>()

const strategiesStore = useStrategiesStore()
const loading = ref(false)

const form = ref({
    name: '',
    is_active: true,
    config: {}
})

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
}

async function handleSubmit() {
    if (!props.strategy) return

    try {
        loading.value = true

        // Валидация для profile_nurture
        if (props.strategy.strategy_type === 'profile_nurture') {
            const nurtureType = form.value.config.nurture_type

            // Очищаем конфигурацию от ненужных полей
            form.value.config = strategiesStore.cleanProfileNurtureConfig(form.value.config)

            // Валидация источника запросов
            if (['search_based', 'mixed_nurture'].includes(nurtureType)) {
                const queriesErrors = strategiesStore.validateQueriesSource(form.value.config.queries_source)
                if (queriesErrors.length > 0) {
                    throw new Error(`Ошибки в источнике запросов: ${queriesErrors.join(', ')}`)
                }
            }

            // Валидация источника сайтов
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

        const strategy = await strategiesStore.updateStrategy(props.strategy.id, {
            name: form.value.name,
            is_active: form.value.is_active,
            config: form.value.config
        })

        emit('updated', strategy)
    } catch (error) {
        console.error('Error updating strategy:', error)
        // Здесь можно добавить уведомление об ошибке пользователю
        alert(`Ошибка при сохранении стратегии: ${error.message}`)
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
