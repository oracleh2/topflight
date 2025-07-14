<!-- frontend/src/views/strategies/StrategiesManager.vue -->
<template>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <!-- Header -->
        <div class="md:flex md:items-center md:justify-between">
            <div class="flex-1 min-w-0">
                <h2 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                    Стратегии нагула и замеров
                </h2>
                <p class="mt-1 text-sm text-gray-500">
                    Создавайте и управляйте стратегиями для прогрева профилей и проверки позиций
                </p>
            </div>
            <div class="mt-4 flex md:mt-0 md:ml-4">
                <button
                    type="button"
                    class="btn-primary"
                    @click="showCreateModal = true"
                >
                    <PlusIcon class="-ml-1 mr-2 h-5 w-5" aria-hidden="true"/>
                    Создать стратегию
                </button>
            </div>
        </div>

        <!-- Strategy Type Tabs -->
        <div class="mt-6">
            <div class="sm:hidden">
                <select
                    v-model="activeTab"
                    class="block w-full rounded-md border-gray-300 focus:border-primary-500 focus:ring-primary-500"
                >
                    <option value="warmup">Стратегии прогрева</option>
                    <option value="position_check">Стратегии замеров</option>
                </select>
            </div>
            <div class="hidden sm:block">
                <nav class="flex space-x-8" aria-label="Tabs">
                    <button
                        @click="activeTab = 'warmup'"
                        :class="[
              activeTab === 'warmup'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
            ]"
                    >
                        Стратегии прогрева ({{ warmupStrategies.length }})
                    </button>
                    <button
                        @click="activeTab = 'position_check'"
                        :class="[
              activeTab === 'position_check'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm'
            ]"
                    >
                        Стратегии замеров ({{ positionStrategies.length }})
                    </button>
                </nav>
            </div>
        </div>

        <!-- Strategies List -->
        <div class="mt-6">
            <div v-if="currentStrategies.length === 0" class="text-center py-12">
                <BeakerIcon class="mx-auto h-12 w-12 text-gray-400"/>
                <h3 class="mt-2 text-sm font-medium text-gray-900">Нет стратегий</h3>
                <p class="mt-1 text-sm text-gray-500">
                    Создайте первую стратегию {{ activeTab === 'warmup' ? 'прогрева' : 'замеров' }}
                </p>
                <div class="mt-6">
                    <button
                        type="button"
                        class="btn-primary"
                        @click="showCreateModal = true"
                    >
                        <PlusIcon class="-ml-1 mr-2 h-5 w-5" aria-hidden="true"/>
                        Создать стратегию
                    </button>
                </div>
            </div>

            <div v-else class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <div
                    v-for="strategy in currentStrategies"
                    :key="strategy.id"
                    class="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
                >
                    <div class="p-6">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <BeakerIcon v-if="strategy.strategy_type === 'warmup'"
                                                class="h-8 w-8 text-blue-500"/>
                                    <ChartBarIcon v-else class="h-8 w-8 text-green-500"/>
                                </div>
                                <div class="ml-4">
                                    <h3 class="text-lg font-medium text-gray-900">
                                        {{ strategy.name }}
                                    </h3>
                                    <p class="text-sm text-gray-500">
                                        {{
                                            strategy.strategy_type === 'warmup' ? 'Прогрев профилей' : 'Проверка позиций'
                                        }}
                                    </p>
                                </div>
                            </div>
                            <div class="flex-shrink-0">
                                <Menu as="div" class="relative inline-block text-left">
                                    <MenuButton
                                        class="-m-2 p-2 rounded-full flex items-center text-gray-400 hover:text-gray-600">
                                        <span class="sr-only">Открыть меню</span>
                                        <EllipsisVerticalIcon class="h-5 w-5" aria-hidden="true"/>
                                    </MenuButton>

                                    <transition
                                        enter-active-class="transition ease-out duration-100"
                                        enter-from-class="transform opacity-0 scale-95"
                                        enter-to-class="transform opacity-100 scale-100"
                                        leave-active-class="transition ease-in duration-75"
                                        leave-from-class="transform opacity-100 scale-100"
                                        leave-to-class="transform opacity-0 scale-95"
                                    >
                                        <MenuItems
                                            class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 divide-y divide-gray-100 focus:outline-none z-10">
                                            <div class="py-1">
                                                <MenuItem v-slot="{ active }">
                                                    <button
                                                        @click="editStrategy(strategy)"
                                                        :class="[
                              active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
                              'group flex items-center px-4 py-2 text-sm w-full text-left'
                            ]"
                                                    >
                                                        <PencilIcon
                                                            class="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500"
                                                            aria-hidden="true"/>
                                                        Редактировать
                                                    </button>
                                                </MenuItem>
                                                <MenuItem v-slot="{ active }">
                                                    <button
                                                        @click="executeStrategy(strategy)"
                                                        :class="[
                              active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
                              'group flex items-center px-4 py-2 text-sm w-full text-left'
                            ]"
                                                    >
                                                        <PlayIcon
                                                            class="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500"
                                                            aria-hidden="true"/>
                                                        Запустить
                                                    </button>
                                                </MenuItem>
                                                <MenuItem v-slot="{ active }">
                                                    <button
                                                        @click="duplicateStrategy(strategy)"
                                                        :class="[
                              active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
                              'group flex items-center px-4 py-2 text-sm w-full text-left'
                            ]"
                                                    >
                                                        <DocumentDuplicateIcon
                                                            class="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500"
                                                            aria-hidden="true"/>
                                                        Дублировать
                                                    </button>
                                                </MenuItem>
                                            </div>
                                            <div class="py-1">
                                                <MenuItem v-slot="{ active }">
                                                    <button
                                                        @click="deleteStrategy(strategy)"
                                                        :class="[
                              active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
                              'group flex items-center px-4 py-2 text-sm w-full text-left'
                            ]"
                                                    >
                                                        <TrashIcon
                                                            class="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500"
                                                            aria-hidden="true"/>
                                                        Удалить
                                                    </button>
                                                </MenuItem>
                                            </div>
                                        </MenuItems>
                                    </transition>
                                </Menu>
                            </div>
                        </div>

                        <!-- Strategy Config Summary -->
                        <div class="mt-4">
                            <StrategyConfigSummary
                                :strategy="strategy"
                                @edit="editStrategy(strategy)"
                            />
                        </div>

                        <!-- Data Sources -->
                        <div class="mt-4">
                            <h4 class="text-sm font-medium text-gray-900 mb-2">Источники
                                данных:</h4>
                            <div class="space-y-1">
                                <div
                                    v-for="source in strategy.data_sources"
                                    :key="source.id"
                                    class="flex items-center text-sm text-gray-600"
                                >
                                    <DocumentIcon class="h-4 w-4 mr-2 text-gray-400"/>
                                    {{ getDataSourceLabel(source.source_type) }}
                                    <span class="ml-auto text-xs text-gray-500">
                    ({{ source.items_count || 0 }} элементов)
                  </span>
                                </div>
                            </div>
                            <button
                                @click="addDataSource(strategy)"
                                class="mt-2 text-sm text-primary-600 hover:text-primary-500"
                            >
                                + Добавить источник данных
                            </button>
                        </div>

                        <!-- Actions -->
                        <div class="mt-6 flex justify-between">
                            <button
                                @click="editStrategy(strategy)"
                                class="btn-secondary text-sm"
                            >
                                Настроить
                            </button>
                            <button
                                @click="executeStrategy(strategy)"
                                class="btn-primary text-sm"
                            >
                                Запустить
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modals -->
        <CreateStrategyModal
            :is-open="showCreateModal"
            :strategy-type="activeTab"
            @close="showCreateModal = false"
            @created="handleStrategyCreated"
        />

        <EditStrategyModal
            :is-open="showEditModal"
            :strategy="selectedStrategy"
            @close="showEditModal = false"
            @updated="handleStrategyUpdated"
        />

        <AddDataSourceModal
            :is-open="showDataSourceModal"
            :strategy="selectedStrategy"
            @close="showDataSourceModal = false"
            @added="handleDataSourceAdded"
        />
    </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {Menu, MenuButton, MenuItem, MenuItems} from '@headlessui/vue'
import {
    PlusIcon,
    BeakerIcon,
    ChartBarIcon,
    EllipsisVerticalIcon,
    PencilIcon,
    PlayIcon,
    DocumentDuplicateIcon,
    TrashIcon,
    DocumentIcon
} from '@heroicons/vue/24/outline'

import {useStrategiesStore} from '@/stores/strategies'
import CreateStrategyModal from '@/components/modals/CreateStrategyModal.vue'
import EditStrategyModal from '@/components/modals/EditStrategyModal.vue'
import AddDataSourceModal from '@/components/modals/AddDataSourceModal.vue'
import StrategyConfigSummary from '@/components/StrategyConfigSummary.vue'

const strategiesStore = useStrategiesStore()

const activeTab = ref('warmup')
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDataSourceModal = ref(false)
const selectedStrategy = ref(null)

const warmupStrategies = computed(() =>
    strategiesStore.strategies.filter(s => s.strategy_type === 'warmup')
)

const positionStrategies = computed(() =>
    strategiesStore.strategies.filter(s => s.strategy_type === 'position_check')
)

const currentStrategies = computed(() =>
    activeTab.value === 'warmup' ? warmupStrategies.value : positionStrategies.value
)

const getDataSourceLabel = (sourceType: string) => {
    const labels = {
        'manual_list': 'Ручной ввод',
        'file_upload': 'Файл',
        'url_import': 'Импорт по URL',
        'google_sheets': 'Google Таблицы',
        'google_docs': 'Google Документы'
    }
    return labels[sourceType] || sourceType
}

const editStrategy = (strategy) => {
    selectedStrategy.value = strategy
    showEditModal.value = true
}

const addDataSource = (strategy) => {
    selectedStrategy.value = strategy
    showDataSourceModal.value = true
}

const executeStrategy = async (strategy) => {
    try {
        await strategiesStore.executeStrategy(strategy.id)
        // Показываем уведомление об успешном запуске
    } catch (error) {
        console.error('Error executing strategy:', error)
    }
}

const duplicateStrategy = async (strategy) => {
    try {
        const newName = `${strategy.name} (копия)`
        await strategiesStore.duplicateStrategy(strategy.id, newName)
    } catch (error) {
        console.error('Error duplicating strategy:', error)
    }
}

const deleteStrategy = async (strategy) => {
    if (confirm(`Удалить стратегию "${strategy.name}"?`)) {
        try {
            await strategiesStore.deleteStrategy(strategy.id)
        } catch (error) {
            console.error('Error deleting strategy:', error)
        }
    }
}

const handleStrategyCreated = () => {
    showCreateModal.value = false
    strategiesStore.fetchStrategies()
}

const handleStrategyUpdated = () => {
    showEditModal.value = false
    selectedStrategy.value = null
    strategiesStore.fetchStrategies()
}

const handleDataSourceAdded = () => {
    showDataSourceModal.value = false
    selectedStrategy.value = null
    strategiesStore.fetchStrategies()
}

onMounted(() => {
    strategiesStore.fetchStrategies()
    strategiesStore.fetchStrategyTemplates()
})
</script>
