<!-- frontend/src/views/strategies/StrategiesManager.vue -->
<template>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
            <!-- Header -->
            <div class="md:flex md:items-center md:justify-between">
                <div class="flex-1 min-w-0">
                    <h1 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                        Управление стратегиями
                    </h1>
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

            <!-- Tabs -->
            <div class="mt-6">
                <div class="sm:hidden">
                    <select
                        v-model="activeTab"
                        class="block w-full rounded-md border-gray-300 focus:border-primary-500 focus:ring-primary-500"
                    >
                        <option value="profile_nurture">Нагул профиля</option>
                        <option value="warmup">Прогрев</option>
                        <option value="position_check">Проверка позиций</option>

                    </select>
                </div>
                <div class="hidden sm:block">
                    <div class="border-b border-gray-200">
                        <nav class="-mb-px flex space-x-8">
                            <button
                                v-for="tab in tabs"
                                :key="tab.key"
                                @click="activeTab = tab.key"
                                :class="[
                                    activeTab === tab.key
                                        ? 'border-primary-500 text-primary-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                                    'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center'
                                ]"
                            >
                                <component
                                    :is="tab.icon"
                                    class="h-5 w-5 mr-2"
                                    :class="activeTab === tab.key ? 'text-primary-500' : 'text-gray-400'"
                                />
                                {{ tab.label }}
                                <span
                                    v-if="tab.count > 0"
                                    :class="[
                                        activeTab === tab.key
                                            ? 'bg-primary-100 text-primary-600'
                                            : 'bg-gray-100 text-gray-900',
                                        'ml-2 py-0.5 px-2.5 rounded-full text-xs font-medium'
                                    ]"
                                >
                                    {{ tab.count }}
                                </span>
                            </button>
                        </nav>
                    </div>
                </div>
            </div>

            <!-- Content -->
            <div class="mt-6">
                <div v-if="loading" class="text-center py-12">
                    <div
                        class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                    <p class="mt-2 text-sm text-gray-500">Загрузка стратегий...</p>
                </div>

                <div v-else-if="error" class="rounded-md bg-red-50 p-4">
                    <div class="flex">
                        <ExclamationTriangleIcon class="h-5 w-5 text-red-400" aria-hidden="true"/>
                        <div class="ml-3">
                            <h3 class="text-sm font-medium text-red-800">Ошибка</h3>
                            <p class="mt-1 text-sm text-red-700">{{ error }}</p>
                        </div>
                    </div>
                </div>

                <div v-else-if="currentStrategies.length === 0" class="text-center py-12">
                    <component
                        :is="getCurrentTabIcon()"
                        class="mx-auto h-12 w-12 text-gray-400"
                    />
                    <h3 class="mt-2 text-sm font-medium text-gray-900">
                        Нет стратегий {{ getCurrentTabLabel() }}
                    </h3>
                    <p class="mt-1 text-sm text-gray-500">
                        Создайте первую стратегию для {{ getCurrentTabDescription() }}
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
                                        <ChartBarIcon
                                            v-else-if="strategy.strategy_type === 'position_check'"
                                            class="h-8 w-8 text-green-500"/>
                                        <UserIcon
                                            v-else-if="strategy.strategy_type === 'profile_nurture'"
                                            class="h-8 w-8 text-purple-500"/>
                                    </div>
                                    <div class="ml-4">
                                        <h3 class="text-lg font-medium text-gray-900">
                                            {{ strategy.name }}
                                        </h3>
                                        <p class="text-sm text-gray-500">
                                            {{
                                                strategiesStore.getStrategyTypeLabel(strategy.strategy_type)
                                            }}
                                        </p>
                                    </div>
                                </div>
                                <div class="flex items-center space-x-2">
                                    <Menu as="div" class="relative inline-block text-left">
                                        <div>
                                            <MenuButton
                                                class="bg-white rounded-full flex items-center text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                                            >
                                                <span class="sr-only">Open options</span>
                                                <EllipsisVerticalIcon class="h-5 w-5"
                                                                      aria-hidden="true"/>
                                            </MenuButton>
                                        </div>
                                        <transition
                                            enter-active-class="transition ease-out duration-100"
                                            enter-from-class="transform opacity-0 scale-95"
                                            enter-to-class="transform opacity-100 scale-100"
                                            leave-active-class="transition ease-in duration-75"
                                            leave-from-class="transform opacity-100 scale-100"
                                            leave-to-class="transform opacity-0 scale-95"
                                        >
                                            <MenuItems
                                                class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                                            >
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
                                                            @click="manageProxies(strategy)"
                                                            :class="[
            active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
            'group flex items-center px-4 py-2 text-sm w-full text-left'
        ]"
                                                        >
                                                            <GlobeAltIcon
                                                                class="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500"
                                                                aria-hidden="true"/>
                                                            Управление прокси
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
                                    @refresh="handleStrategyRefresh"
                                />
                            </div>

                            <!-- Data Sources -->
                            <div v-if="strategy.strategy_type !== 'profile_nurture'" class="mt-4">
                                <h4 class="text-sm font-medium text-gray-900 mb-2">Источники
                                    данных:</h4>
                                <div class="space-y-1">
                                    <div
                                        v-if="strategy.data_sources.length > 0"
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
                                    <div v-else class="text-sm text-gray-500">
                                        Нет источников данных
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
                            <div class="mt-4 flex justify-between">
                                <span
                                    :class="[
                                        strategy.is_active ? 'text-green-600' : 'text-gray-400',
                                        'text-xs font-medium'
                                    ]"
                                >
                                    {{ strategy.is_active ? 'Активна' : 'Неактивна' }}
                                </span>
                                <div class="flex space-x-2">
                                    <button
                                        @click="editStrategy(strategy)"
                                        class="text-xs text-primary-600 hover:text-primary-500"
                                    >
                                        Настроить
                                    </button>
                                    <button
                                        @click="executeStrategy(strategy)"
                                        class="text-xs text-green-600 hover:text-green-500"
                                    >
                                        Запустить
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Mass Actions for Profile Nurture Strategies -->
        <div v-if="activeTab === 'profile_nurture' && currentStrategies.length > 0"
             class="mt-8 border-t pt-6">
            <div class="bg-gray-50 rounded-lg p-6">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h3 class="text-lg font-medium text-gray-900">
                            Массовые действия
                        </h3>
                        <p class="text-sm text-gray-600">
                            Управление всеми стратегиями нагула профилей
                        </p>
                    </div>
                    <div class="flex space-x-3">
                        <button
                            @click="refreshAllStrategiesStatus"
                            :disabled="refreshingStatus"
                            class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                        >
                            <div
                                v-if="refreshingStatus"
                                class="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"
                            ></div>
                            <ArrowPathIcon v-else class="h-4 w-4 mr-2"/>
                            {{ refreshingStatus ? 'Обновление...' : 'Обновить статус' }}
                        </button>

                        <button
                            @click="maintainAllStrategies"
                            :disabled="maintainingAll"
                            class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                        >
                            <div
                                v-if="maintainingAll"
                                class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"
                            ></div>
                            <PlayIcon v-else class="h-4 w-4 mr-2"/>
                            {{ maintainingAll ? 'Поддержание...' : 'Поддержать все стратегии' }}
                        </button>
                    </div>
                </div>

                <!-- Статистика стратегий -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="bg-white rounded-lg p-4 border">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <UserIcon class="h-8 w-8 text-gray-400"/>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm font-medium text-gray-500">Всего стратегий</p>
                                <p class="text-lg font-semibold text-gray-900">
                                    {{ currentStrategies.length }}</p>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-lg p-4 border">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <ExclamationTriangleIcon class="h-8 w-8 text-red-400"/>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm font-medium text-gray-500">Критических</p>
                                <p class="text-lg font-semibold text-red-600">
                                    {{ criticalStrategiesCount }}</p>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-lg p-4 border">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <CheckCircleIcon class="h-8 w-8 text-green-400"/>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm font-medium text-gray-500">Нормальных</p>
                                <p class="text-lg font-semibold text-green-600">
                                    {{ normalStrategiesCount }}</p>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-lg p-4 border">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <ClockIcon class="h-8 w-8 text-blue-400"/>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm font-medium text-gray-500">Нужен нагул</p>
                                <p class="text-lg font-semibold text-blue-600">{{
                                        needNurtureCount
                                    }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Strategy Modal -->
        <CreateStrategyModal
            :is-open="showCreateModal"
            :strategy-type="activeTab"
            @close="showCreateModal = false"
            @created="handleStrategyCreated"
        />

        <!-- Edit Strategy Modal -->
        <EditStrategyModal
            :is-open="showEditModal"
            :strategy="selectedStrategy"
            @close="showEditModal = false"
            @updated="handleStrategyUpdated"
        >
        </EditStrategyModal>

        <!-- Add Data Source Modal -->
        <AddDataSourceModal
            :is-open="showAddDataSourceModal"
            :strategy="selectedStrategy"
            @close="showAddDataSourceModal = false"
            @added="handleDataSourceAdded"
        />

        <!-- Proxy Manager Modal -->
        <ProxyManagerModal
            :is-open="showProxyManagerModal"
            :strategy="selectedStrategy"
            @close="showProxyManagerModal = false"
        />
    </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted} from 'vue'
import {
    PlusIcon,
    BeakerIcon,
    ChartBarIcon,
    UserIcon,
    ExclamationTriangleIcon,
    EllipsisVerticalIcon,
    PencilIcon,
    PlayIcon,
    DocumentDuplicateIcon,
    TrashIcon,
    DocumentIcon,
    GlobeAltIcon,
    ArrowPathIcon,
    CheckCircleIcon,
    ClockIcon

} from '@heroicons/vue/24/outline'
import {Menu, MenuButton, MenuItem, MenuItems} from '@headlessui/vue'
import {useStrategiesStore} from '@/stores/strategies'
import type {Strategy} from '@/stores/strategies'
import CreateStrategyModal from '@/components/strategies/CreateStrategyModal.vue'
import EditStrategyModal from '@/components/strategies/EditStrategyModal.vue'
import StrategyConfigSummary from '@/components/strategies/StrategyConfigSummary.vue'
import AddDataSourceModal from '@/components/modals/AddDataSourceModal.vue'
import StrategyProxyManager from '@/components/strategies/StrategyProxyManager.vue'
import ProxyManagerModal from "@/components/strategies/ProxyManagerModal.vue";
import {api} from '@/api'


const strategiesStore = useStrategiesStore()

const activeTab = ref<'warmup' | 'position_check' | 'profile_nurture'>('profile_nurture')
const showCreateModal = ref(false)
const showEditModal = ref(false)
const selectedStrategy = ref<Strategy | null>(null)
const showAddDataSourceModal = ref(false)
const showProxyManagerModal = ref(false)
const refreshingStatus = ref(false)
const maintainingAll = ref(false)


const tabs = computed(() => [
    {
        key: 'profile_nurture',
        label: 'Нагул профиля',
        icon: UserIcon,
        count: strategiesStore.profileNurtureStrategies.length
    },
    {
        key: 'warmup',
        label: 'Прогрев',
        icon: BeakerIcon,
        count: strategiesStore.warmupStrategies.length
    },
    {
        key: 'position_check',
        label: 'Проверка позиций',
        icon: ChartBarIcon,
        count: strategiesStore.positionCheckStrategies.length
    },

])

const currentStrategies = computed(() => {
    switch (activeTab.value) {
        case 'profile_nurture':
            return strategiesStore.profileNurtureStrategies
        case 'warmup':
            return strategiesStore.warmupStrategies
        case 'position_check':
            return strategiesStore.positionCheckStrategies
        default:
            return []
    }
})

const criticalStrategiesCount = computed(() => {
    return currentStrategies.value.filter(s =>
        s.strategy_type === 'profile_nurture' && s.nurture_status?.status === 'critical'
    ).length
})

const normalStrategiesCount = computed(() => {
    return currentStrategies.value.filter(s =>
        s.strategy_type === 'profile_nurture' && s.nurture_status?.status === 'normal'
    ).length
})

const needNurtureCount = computed(() => {
    return currentStrategies.value.filter(s =>
        s.strategy_type === 'profile_nurture' && s.nurture_status?.needs_nurture
    ).length
})

const {loading, error} = strategiesStore

async function handleStrategyRefresh() {
    await strategiesStore.fetchStrategies()
}

function getCurrentTabIcon() {
    const tab = tabs.value.find(t => t.key === activeTab.value)
    return tab?.icon || BeakerIcon
}

function getCurrentTabLabel(): string {
    switch (activeTab.value) {
        case 'warmup':
            return 'прогрева'
        case 'position_check':
            return 'проверки позиций'
        case 'profile_nurture':
            return 'нагула профиля'
        default:
            return ''
    }
}

function getCurrentTabDescription(): string {
    switch (activeTab.value) {
        case 'warmup':
            return 'прогрева сайтов'
        case 'position_check':
            return 'проверки позиций'
        case 'profile_nurture':
            return 'нагула профилей'
        default:
            return ''
    }
}

function getSourceTypeLabel(type: string): string {
    switch (type) {
        case 'manual_list':
            return 'Ручной ввод'
        case 'file_upload':
            return 'Загрузка файла'
        case 'url_import':
            return 'URL источник'
        case 'google_sheets':
            return 'Google Таблицы'
        case 'google_docs':
            return 'Google Документы'
        default:
            return type
    }
}

function editStrategy(strategy: Strategy) {
    selectedStrategy.value = strategy
    showEditModal.value = true
}

async function executeStrategy(strategy: Strategy) {
    try {
        await strategiesStore.executeStrategy(strategy.id)
        // Показать уведомление об успешном запуске
        console.log('Strategy executed successfully')
    } catch (error) {
        console.error('Error executing strategy:', error)
        // Показать уведомление об ошибке
    }
}

async function duplicateStrategy(strategy: Strategy) {
    try {
        await strategiesStore.createStrategy({
            name: `${strategy.name} (копия)`,
            strategy_type: strategy.strategy_type,
            config: {...strategy.config}
        })
        // Показать уведомление об успешном дублировании
        console.log('Strategy duplicated successfully')
    } catch (error) {
        console.error('Error duplicating strategy:', error)
        // Показать уведомление об ошибке
    }
}

async function deleteStrategy(strategy: Strategy) {
    if (confirm(`Вы уверены, что хотите удалить стратегию "${strategy.name}"?`)) {
        try {
            await strategiesStore.deleteStrategy(strategy.id)
            // Показать уведомление об успешном удалении
            console.log('Strategy deleted successfully')
        } catch (error) {
            console.error('Error deleting strategy:', error)
            // Показать уведомление об ошибке
        }
    }
}

function handleStrategyCreated(strategy: Strategy) {
    showCreateModal.value = false
    // Обновляем список стратегий
    strategiesStore.fetchStrategies()
}

function handleStrategyUpdated(strategy: Strategy) {
    showEditModal.value = false
    selectedStrategy.value = null
    // Обновляем список стратегий
    strategiesStore.fetchStrategies()
}

// Функция для добавления источника данных
function addDataSource(strategy: Strategy) {
    selectedStrategy.value = strategy
    showAddDataSourceModal.value = true
}

// Функция получения метки источника данных
function getDataSourceLabel(sourceType: string): string {
    const labels: Record<string, string> = {
        'manual_list': 'Ручной ввод',
        'file_upload': 'Загрузка файла',
        'url_import': 'Импорт по URL',
        'google_sheets': 'Google Таблицы',
        'google_docs': 'Google Документы'
    }
    return labels[sourceType] || sourceType
}

// Обработчик добавления источника данных
function handleDataSourceAdded() {
    showAddDataSourceModal.value = false
    selectedStrategy.value = null
    strategiesStore.fetchStrategies()
}

function manageProxies(strategy: Strategy) {
    selectedStrategy.value = strategy
    showProxyManagerModal.value = true
}

async function refreshAllStrategiesStatus() {
    refreshingStatus.value = true
    try {
        await strategiesStore.fetchStrategies()
        console.log('Статус всех стратегий обновлен')
    } catch (error) {
        console.error('Ошибка обновления статуса:', error)
    } finally {
        refreshingStatus.value = false
    }
}

async function maintainAllStrategies() {
    maintainingAll.value = true
    try {
        const response = await strategiesStore.maintainAllStrategies()

        if (response.success) {
            console.log(`Поддержано ${response.maintained_strategies} стратегий`)
            await strategiesStore.fetchStrategies()
        } else {
            console.error('Ошибка автоматического поддержания')
        }
    } catch (error) {
        console.error('Ошибка поддержания стратегий:', error)
    } finally {
        maintainingAll.value = false
    }
}

onMounted(async () => {
    await Promise.all([
        strategiesStore.fetchStrategies(),
        strategiesStore.fetchStrategyTemplates(),
    ])
})
</script>
