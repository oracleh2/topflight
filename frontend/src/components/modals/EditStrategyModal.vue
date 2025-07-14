<!-- frontend/src/components/modals/EditStrategyModal.vue -->
<template>
    <TransitionRoot as="template" :show="isOpen">
        <Dialog as="div" class="relative z-10" @close="$emit('close')">
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
                            class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:p-6">
                            <form @submit.prevent="handleSubmit">
                                <div>
                                    <div
                                        class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
                                        <PencilIcon class="h-6 w-6 text-primary-600"
                                                    aria-hidden="true"/>
                                    </div>
                                    <div class="mt-3 text-center sm:mt-5">
                                        <DialogTitle as="h3"
                                                     class="text-base font-semibold leading-6 text-gray-900">
                                            Редактировать стратегию {{ strategyTypeLabel }}
                                        </DialogTitle>
                                        <div class="mt-2">
                                            <p class="text-sm text-gray-500">
                                                Настройте стратегию для {{
                                                    strategy?.strategy_type === 'warmup' ? 'прогрева профилей' : 'проверки позиций'
                                                }}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                <div class="mt-6 space-y-6">
                                    <!-- Название стратегии -->
                                    <div>
                                        <label for="strategy-name"
                                               class="block text-sm font-medium text-gray-700 mb-2">
                                            Название стратегии *
                                        </label>
                                        <input
                                            id="strategy-name"
                                            v-model="form.name"
                                            type="text"
                                            required
                                            maxlength="255"
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            placeholder="Введите название стратегии"
                                        />
                                    </div>

                                    <!-- Статус стратегии -->
                                    <div>
                                        <label class="flex items-center">
                                            <input
                                                v-model="form.is_active"
                                                type="checkbox"
                                                class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                            />
                                            <span class="ml-2 text-sm text-gray-700">Активная стратегия</span>
                                        </label>
                                    </div>

                                    <!-- Конфигурация стратегии прогрева -->
                                    <div v-if="strategy?.strategy_type === 'warmup'"
                                         class="space-y-4">
                                        <h4 class="text-md font-medium text-gray-900">Настройки
                                            прогрева</h4>

                                        <!-- Тип стратегии -->
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                Тип стратегии прогрева *
                                            </label>
                                            <select
                                                v-model="form.config.type"
                                                required
                                                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            >
                                                <option value="direct">Только прямые заходы</option>
                                                <option value="search">Только поиск в Яндексе
                                                </option>
                                                <option value="mixed">Комбинированная стратегия
                                                </option>
                                            </select>
                                        </div>

                                        <!-- Пропорции для mixed стратегии -->
                                        <div v-if="form.config.type === 'mixed'"
                                             class="grid grid-cols-2 gap-4">
                                            <div>
                                                <label
                                                    class="block text-sm font-medium text-gray-700 mb-1">
                                                    Прямые заходы
                                                </label>
                                                <input
                                                    v-model.number="form.config.proportions.direct_visits"
                                                    type="number"
                                                    min="1"
                                                    max="20"
                                                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                />
                                            </div>
                                            <div>
                                                <label
                                                    class="block text-sm font-medium text-gray-700 mb-1">
                                                    Поисковые заходы
                                                </label>
                                                <input
                                                    v-model.number="form.config.proportions.search_visits"
                                                    type="number"
                                                    min="1"
                                                    max="20"
                                                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                />
                                            </div>
                                        </div>

                                        <!-- Настройки поиска -->
                                        <div
                                            v-if="form.config.type === 'search' || form.config.type === 'mixed'">
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                Домены Яндекса для поиска
                                            </label>
                                            <div class="space-y-2">
                                                <label
                                                    v-for="domain in yandexDomains"
                                                    :key="domain.value"
                                                    class="flex items-center"
                                                >
                                                    <input
                                                        v-model="form.config.search_config.yandex_domains"
                                                        type="checkbox"
                                                        :value="domain.value"
                                                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                                    />
                                                    <span class="ml-2 text-sm text-gray-700">{{
                                                            domain.label
                                                        }}</span>
                                                </label>
                                            </div>
                                        </div>

                                        <!-- Дополнительные настройки прогрева -->
                                        <div class="border-t pt-4">
                                            <h5 class="text-sm font-medium text-gray-900 mb-3">
                                                Поведенческие настройки</h5>

                                            <div class="grid grid-cols-2 gap-4">
                                                <div>
                                                    <label
                                                        class="block text-sm font-medium text-gray-700 mb-1">
                                                        Время на сайте (мин)
                                                    </label>
                                                    <div class="grid grid-cols-2 gap-2">
                                                        <input
                                                            v-model.number="form.config.direct_config.time_per_site.min"
                                                            type="number"
                                                            min="1"
                                                            placeholder="От"
                                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                        />
                                                        <input
                                                            v-model.number="form.config.direct_config.time_per_site.max"
                                                            type="number"
                                                            min="1"
                                                            placeholder="До"
                                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                        />
                                                    </div>
                                                </div>

                                                <div>
                                                    <label
                                                        class="block text-sm font-medium text-gray-700 mb-1">
                                                        Сайтов за сессию
                                                    </label>
                                                    <div class="grid grid-cols-2 gap-2">
                                                        <input
                                                            v-model.number="form.config.direct_config.sites_per_session.min"
                                                            type="number"
                                                            min="1"
                                                            placeholder="От"
                                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                        />
                                                        <input
                                                            v-model.number="form.config.direct_config.sites_per_session.max"
                                                            type="number"
                                                            min="1"
                                                            placeholder="До"
                                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Конфигурация стратегии проверки позиций -->
                                    <div v-if="strategy?.strategy_type === 'position_check'"
                                         class="space-y-4">
                                        <h4 class="text-md font-medium text-gray-900">Настройки
                                            проверки позиций</h4>

                                        <!-- Частота проверки -->
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                Частота проверки
                                            </label>
                                            <select
                                                v-model="form.config.check_frequency"
                                                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            >
                                                <option value="daily">Ежедневно</option>
                                                <option value="weekly">Еженедельно</option>
                                                <option value="monthly">Ежемесячно</option>
                                                <option value="custom">Пользовательское расписание
                                                </option>
                                            </select>
                                        </div>

                                        <!-- Количество страниц для проверки -->
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                Количество страниц для проверки
                                            </label>
                                            <input
                                                v-model.number="form.config.search_config.pages_to_check"
                                                type="number"
                                                min="1"
                                                max="50"
                                                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                            />
                                        </div>

                                        <!-- Типы устройств -->
                                        <div>
                                            <label
                                                class="block text-sm font-medium text-gray-700 mb-2">
                                                Типы устройств
                                            </label>
                                            <div class="space-y-2">
                                                <label class="flex items-center">
                                                    <input
                                                        v-model="form.config.search_config.device_types"
                                                        type="checkbox"
                                                        value="desktop"
                                                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                                    />
                                                    <span
                                                        class="ml-2 text-sm text-gray-700">Десктоп</span>
                                                </label>
                                                <label class="flex items-center">
                                                    <input
                                                        v-model="form.config.search_config.device_types"
                                                        type="checkbox"
                                                        value="mobile"
                                                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                                    />
                                                    <span class="ml-2 text-sm text-gray-700">Мобильное</span>
                                                </label>
                                            </div>
                                        </div>

                                        <!-- Дополнительные настройки проверки позиций -->
                                        <div class="border-t pt-4">
                                            <h5 class="text-sm font-medium text-gray-900 mb-3">
                                                Поведенческие настройки</h5>

                                            <div class="space-y-3">
                                                <label class="flex items-center">
                                                    <input
                                                        v-model="form.config.behavior.scroll_serp"
                                                        type="checkbox"
                                                        class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                                    />
                                                    <span class="ml-2 text-sm text-gray-700">Прокручивать SERP</span>
                                                </label>

                                                <div>
                                                    <label
                                                        class="block text-sm font-medium text-gray-700 mb-1">
                                                        Время на SERP (сек)
                                                    </label>
                                                    <div class="grid grid-cols-2 gap-2">
                                                        <input
                                                            v-model.number="form.config.behavior.time_on_serp.min"
                                                            type="number"
                                                            min="1"
                                                            placeholder="От"
                                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                        />
                                                        <input
                                                            v-model.number="form.config.behavior.time_on_serp.max"
                                                            type="number"
                                                            min="1"
                                                            placeholder="До"
                                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="mt-6 flex justify-end space-x-3">
                                    <button
                                        type="button"
                                        class="btn-secondary"
                                        @click="$emit('close')"
                                    >
                                        Отмена
                                    </button>
                                    <button
                                        type="submit"
                                        class="btn-primary"
                                        :disabled="loading || !form.name"
                                    >
                                        <Spinner v-if="loading" class="w-4 h-4 mr-2"/>
                                        Сохранить изменения
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
import {PencilIcon} from '@heroicons/vue/24/outline'

import {useStrategiesStore} from '@/stores/strategies'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
    isOpen: boolean
    strategy: any | null
}

interface Emits {
    (e: 'close'): void

    (e: 'updated', strategy: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const strategiesStore = useStrategiesStore()

const loading = ref(false)

const strategyTypeLabel = computed(() =>
    props.strategy?.strategy_type === 'warmup' ? 'прогрева' : 'проверки позиций'
)

const yandexDomains = [
    {value: 'yandex.ru', label: 'Яндекс.Россия (yandex.ru)'},
    {value: 'yandex.by', label: 'Яндекс.Беларусь (yandex.by)'},
    {value: 'yandex.kz', label: 'Яндекс.Казахстан (yandex.kz)'},
    {value: 'yandex.ua', label: 'Яндекс.Украина (yandex.ua)'}
]

const form = ref({
    name: '',
    is_active: true,
    config: {}
})

function resetForm() {
    if (props.strategy) {
        form.value = {
            name: props.strategy.name,
            is_active: props.strategy.is_active ?? true,
            config: JSON.parse(JSON.stringify(props.strategy.config))
        }
    }
}

async function handleSubmit() {
    if (!props.strategy) return

    try {
        loading.value = true

        const strategy = await strategiesStore.updateStrategy(props.strategy.id, {
            name: form.value.name,
            is_active: form.value.is_active,
            config: form.value.config
        })

        emit('updated', strategy)
    } catch (error) {
        console.error('Error updating strategy:', error)
        // Здесь можно добавить уведомление об ошибке
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
