<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
                <h1 class="text-xl font-semibold text-gray-900">Профили</h1>
                <p class="mt-2 text-sm text-gray-700">
                    Управление браузерными профилями для парсинга
                </p>
            </div>
            <div class="mt-4 sm:mt-0 flex space-x-3">
                <button
                    v-if="selectedProfiles.length > 0"
                    @click="showBulkDeleteModal = true"
                    class="btn-danger"
                >
                    Удалить выбранные ({{ selectedProfiles.length }})
                </button>
                <button
                    @click="refreshProfiles"
                    class="btn-secondary"
                    :disabled="loading"
                >
                    <ArrowPathIcon class="h-4 w-4 mr-2" :class="{ 'animate-spin': loading }"/>
                    Обновить
                </button>
            </div>
        </div>

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <UserCircleIcon class="h-6 w-6 text-gray-400"/>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">
                                    Всего профилей
                                </dt>
                                <dd class="text-lg font-medium text-gray-900">
                                    {{ stats.total || 0 }}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <CheckCircleIcon class="h-6 w-6 text-green-400"/>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">
                                    Прогретых
                                </dt>
                                <dd class="text-lg font-medium text-gray-900">
                                    {{ stats.warmed_up || 0 }}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <ComputerDesktopIcon class="h-6 w-6 text-blue-400"/>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">
                                    Desktop
                                </dt>
                                <dd class="text-lg font-medium text-gray-900">
                                    {{ stats.desktop || 0 }}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <DevicePhoneMobileIcon class="h-6 w-6 text-indigo-400"/>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">
                                    Mobile
                                </dt>
                                <dd class="text-lg font-medium text-gray-900">
                                    {{ stats.mobile || 0 }}
                                </dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Filters -->
        <div class="bg-white shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
                    <!-- Search -->
                    <div class="lg:col-span-2">
                        <label class="block text-sm font-medium text-gray-700">
                            Поиск
                        </label>
                        <div class="mt-1 relative rounded-md shadow-sm">
                            <div
                                class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <MagnifyingGlassIcon class="h-5 w-5 text-gray-400"/>
                            </div>
                            <input
                                v-model="filters.search"
                                type="text"
                                placeholder="Поиск по названию, User Agent..."
                                class="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
                                @input="debounceSearch"
                            />
                        </div>
                    </div>

                    <!-- Device Type Filter -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700">
                            Тип устройства
                        </label>
                        <select
                            v-model="filters.device_type"
                            @change="applyFilters"
                            class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                        >
                            <option value="">Все типы</option>
                            <option value="desktop">Desktop</option>
                            <option value="mobile">Mobile</option>
                            <option value="tablet">Tablet</option>
                        </select>
                    </div>

                    <!-- Status Filter -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700">
                            Статус
                        </label>
                        <select
                            v-model="filters.status"
                            @change="applyFilters"
                            class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                        >
                            <option value="">Все статусы</option>
                            <option value="active">Активный</option>
                            <option value="inactive">Неактивный</option>
                            <option value="corrupted">Испорченный</option>
                        </select>
                    </div>

                    <!-- Warmup Status Filter -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700">
                            Прогрев
                        </label>
                        <select
                            v-model="filters.is_warmed_up"
                            @change="applyFilters"
                            class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                        >
                            <option value="">Все</option>
                            <option value="true">Прогрет</option>
                            <option value="false">Не прогрет</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>

        <!-- Profiles Table -->
        <div class="bg-white shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center">
                        <h3 class="text-lg font-medium text-gray-900">
                            Профили
                        </h3>
                        <span class="ml-2 text-sm text-gray-500">
              ({{
                                pagination.total
                            }} {{
                                declension(pagination.total, ['профиль', 'профиля', 'профилей'])
                            }})
            </span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <label class="text-sm text-gray-700">
                            Показывать по:
                        </label>
                        <select
                            v-model="pagination.per_page"
                            @change="applyFilters"
                            class="text-sm border-gray-300 rounded-md"
                        >
                            <option value="20">20</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                        </select>
                    </div>
                </div>

                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                <input
                                    type="checkbox"
                                    :checked="allSelected"
                                    @change="toggleSelectAll"
                                    class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                                />
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                @click="sortBy('name')">
                                <div class="flex items-center">
                                    Название
                                    <ArrowUpIcon
                                        v-if="sorting.sort_by === 'name' && sorting.sort_order === 'asc'"
                                        class="ml-1 h-4 w-4"/>
                                    <ArrowDownIcon
                                        v-if="sorting.sort_by === 'name' && sorting.sort_order === 'desc'"
                                        class="ml-1 h-4 w-4"/>
                                </div>
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                @click="sortBy('device_type')">
                                <div class="flex items-center">
                                    Устройство
                                    <ArrowUpIcon
                                        v-if="sorting.sort_by === 'device_type' && sorting.sort_order === 'asc'"
                                        class="ml-1 h-4 w-4"/>
                                    <ArrowDownIcon
                                        v-if="sorting.sort_by === 'device_type' && sorting.sort_order === 'desc'"
                                        class="ml-1 h-4 w-4"/>
                                </div>
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                @click="sortBy('created_at')">
                                <div class="flex items-center">
                                    Дата создания
                                    <ArrowUpIcon
                                        v-if="sorting.sort_by === 'created_at' && sorting.sort_order === 'asc'"
                                        class="ml-1 h-4 w-4"/>
                                    <ArrowDownIcon
                                        v-if="sorting.sort_by === 'created_at' && sorting.sort_order === 'desc'"
                                        class="ml-1 h-4 w-4"/>
                                </div>
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                @click="sortBy('cookies_count')">
                                <div class="flex items-center">
                                    Куки
                                    <ArrowUpIcon
                                        v-if="sorting.sort_by === 'cookies_count' && sorting.sort_order === 'asc'"
                                        class="ml-1 h-4 w-4"/>
                                    <ArrowDownIcon
                                        v-if="sorting.sort_by === 'cookies_count' && sorting.sort_order === 'desc'"
                                        class="ml-1 h-4 w-4"/>
                                </div>
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Стратегия нагула
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Статус
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                                @click="sortBy('last_used')">
                                <div class="flex items-center">
                                    Последнее использование
                                    <ArrowUpIcon
                                        v-if="sorting.sort_by === 'last_used' && sorting.sort_order === 'asc'"
                                        class="ml-1 h-4 w-4"/>
                                    <ArrowDownIcon
                                        v-if="sorting.sort_by === 'last_used' && sorting.sort_order === 'desc'"
                                        class="ml-1 h-4 w-4"/>
                                </div>
                            </th>
                            <th class="relative px-6 py-3">
                                <span class="sr-only">Действия</span>
                            </th>
                        </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                        <tr v-if="loading">
                            <td colspan="9" class="px-6 py-4 text-center text-sm text-gray-500">
                                <div class="flex justify-center">
                                    <ArrowPathIcon class="h-5 w-5 animate-spin"/>
                                    <span class="ml-2">Загрузка...</span>
                                </div>
                            </td>
                        </tr>
                        <tr v-else-if="profiles.length === 0">
                            <td colspan="9" class="px-6 py-4 text-center text-sm text-gray-500">
                                Профили не найдены
                            </td>
                        </tr>
                        <tr
                            v-else
                            v-for="profile in profiles"
                            :key="profile.id"
                            :class="[
                  selectedProfiles.includes(profile.id) ? 'bg-blue-50' : 'hover:bg-gray-50',
                  'cursor-pointer'
                ]"
                            @click="selectProfile(profile.id)"
                        >
                            <td class="px-6 py-4 whitespace-nowrap">
                                <input
                                    type="checkbox"
                                    :checked="selectedProfiles.includes(profile.id)"
                                    @click.stop
                                    @change="toggleProfile(profile.id)"
                                    class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                                />
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="flex items-center">
                                    <div class="flex-shrink-0">
                                        <UserCircleIcon class="h-8 w-8 text-gray-400"/>
                                    </div>
                                    <div class="ml-4">
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ profile.name }}
                                        </div>
                                        <div class="text-sm text-gray-500">
                                            ID: {{ profile.id.substring(0, 8) }}...
                                        </div>
                                    </div>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="flex items-center">
                                    <ComputerDesktopIcon v-if="profile.device_type === 'desktop'"
                                                         class="h-5 w-5 text-blue-500 mr-2"/>
                                    <DevicePhoneMobileIcon
                                        v-else-if="profile.device_type === 'mobile'"
                                        class="h-5 w-5 text-indigo-500 mr-2"/>
                                    <DeviceTabletIcon v-else class="h-5 w-5 text-purple-500 mr-2"/>
                                    <span class="text-sm text-gray-900 capitalize">
                      {{ profile.device_type }}
                    </span>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {{ formatDate(profile.created_at) }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {{ profile.cookies_count }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                  <span
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {{ profile.nurture_strategy }}
                  </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="[
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    getStatusClass(profile)
                  ]">
                    {{ getStatusText(profile) }}
                  </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {{ profile.last_used ? formatDate(profile.last_used) : 'Никогда' }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <div class="flex items-center space-x-2">
                                    <button
                                        @click.stop="openProfile(profile.id)"
                                        class="text-primary-600 hover:text-primary-900"
                                    >
                                        <EyeIcon class="h-4 w-4"/>
                                    </button>
                                    <button
                                        @click.stop="confirmDeleteProfile(profile)"
                                        class="text-red-600 hover:text-red-900"
                                    >
                                        <TrashIcon class="h-4 w-4"/>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Pagination -->
                <div v-if="pagination.total_pages > 1"
                     class="mt-6 flex items-center justify-between">
                    <div class="flex-1 flex justify-between sm:hidden">
                        <button
                            @click="changePage(pagination.page - 1)"
                            :disabled="pagination.page === 1"
                            class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                        >
                            Назад
                        </button>
                        <button
                            @click="changePage(pagination.page + 1)"
                            :disabled="pagination.page === pagination.total_pages"
                            class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                        >
                            Далее
                        </button>
                    </div>
                    <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                        <div>
                            <p class="text-sm text-gray-700">
                                Показано
                                <span class="font-medium">{{
                                        ((pagination.page - 1) * pagination.per_page) + 1
                                    }}</span>
                                -
                                <span class="font-medium">{{
                                        Math.min(pagination.page * pagination.per_page, pagination.total)
                                    }}</span>
                                из
                                <span class="font-medium">{{ pagination.total }}</span>
                                результатов
                            </p>
                        </div>
                        <div>
                            <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                                <button
                                    @click="changePage(pagination.page - 1)"
                                    :disabled="pagination.page === 1"
                                    class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                >
                                    <ChevronLeftIcon class="h-5 w-5"/>
                                </button>
                                <button
                                    v-for="page in visiblePages"
                                    :key="page"
                                    @click="changePage(page)"
                                    :class="[
                    page === pagination.page
                      ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                      : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50',
                    'relative inline-flex items-center px-4 py-2 border text-sm font-medium'
                  ]"
                                >
                                    {{ page }}
                                </button>
                                <button
                                    @click="changePage(pagination.page + 1)"
                                    :disabled="pagination.page === pagination.total_pages"
                                    class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                                >
                                    <ChevronRightIcon class="h-5 w-5"/>
                                </button>
                            </nav>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div v-if="showDeleteModal"
             class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3 text-center">
                    <div
                        class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                        <ExclamationTriangleIcon class="h-6 w-6 text-red-600"/>
                    </div>
                    <h3 class="text-lg font-medium text-gray-900 mt-2">Подтвердите удаление</h3>
                    <div class="mt-2 px-7 py-3">
                        <p class="text-sm text-gray-500">
                            Вы уверены, что хотите удалить профиль "{{ profileToDelete?.name }}"?
                            Это действие нельзя отменить.
                        </p>
                    </div>
                    <div class="flex justify-center space-x-4 mt-4">
                        <button
                            @click="showDeleteModal = false"
                            class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                        >
                            Отмена
                        </button>
                        <button
                            @click="deleteProfile"
                            class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
                        >
                            Удалить
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Bulk Delete Modal -->
        <div v-if="showBulkDeleteModal"
             class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3 text-center">
                    <div
                        class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                        <ExclamationTriangleIcon class="h-6 w-6 text-red-600"/>
                    </div>
                    <h3 class="text-lg font-medium text-gray-900 mt-2">Массовое удаление</h3>
                    <div class="mt-2 px-7 py-3">
                        <p class="text-sm text-gray-500">
                            Вы уверены, что хотите удалить {{ selectedProfiles.length }}
                            {{
                                declension(selectedProfiles.length, ['профиль', 'профиля', 'профилей'])
                            }}?
                            Это действие нельзя отменить.
                        </p>
                    </div>
                    <div class="flex justify-center space-x-4 mt-4">
                        <button
                            @click="showBulkDeleteModal = false"
                            class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                        >
                            Отмена
                        </button>
                        <button
                            @click="bulkDeleteProfiles"
                            class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
                        >
                            Удалить все
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, onMounted, computed} from 'vue'
import {useRouter} from 'vue-router'
import {useNotifications} from '@/composables/useNotifications'
import {api} from '@/api'
import {
    UserCircleIcon,
    CheckCircleIcon,
    ComputerDesktopIcon,
    DevicePhoneMobileIcon,
    DeviceTabletIcon,
    ArrowPathIcon,
    MagnifyingGlassIcon,
    ArrowUpIcon,
    ArrowDownIcon,
    EyeIcon,
    TrashIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
    ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline'

// Types
interface Profile {
    id: string
    name: string
    device_type: string
    created_at: string
    cookies_count: number
    visited_sites_count: number
    nurture_strategy: string
    status: string
    is_warmed_up: boolean
    last_used: string | null
    user_agent: string
    proxy_assigned: boolean
    corruption_reason: string | null
}

interface Stats {
    total: number
    warmed_up: number
    desktop: number
    mobile: number
    corrupted: number
    ready_to_use: number
}

// Composables
const router = useRouter()
const {showNotification} = useNotifications()

// Reactive state
const profiles = ref<Profile[]>([])
const stats = ref<Stats>({
    total: 0,
    warmed_up: 0,
    desktop: 0,
    mobile: 0,
    corrupted: 0,
    ready_to_use: 0,
})
const loading = ref(false)
const selectedProfiles = ref<string[]>([])
const showDeleteModal = ref(false)
const showBulkDeleteModal = ref(false)
const profileToDelete = ref<Profile | null>(null)

// Filters
const filters = ref({
    search: '',
    device_type: '',
    status: '',
    is_warmed_up: '',
})

// Sorting
const sorting = ref({
    sort_by: 'created_at',
    sort_order: 'desc',
})

// Pagination
const pagination = ref({
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0,
})

// Computed
const allSelected = computed(() => {
    return profiles.value.length > 0 && selectedProfiles.value.length === profiles.value.length
})

const visiblePages = computed(() => {
    const current = pagination.value.page
    const total = pagination.value.total_pages
    const pages = []

    // Always show first page
    if (current > 3) pages.push(1)
    if (current > 4) pages.push('...')

    // Show pages around current
    for (let i = Math.max(1, current - 2); i <= Math.min(total, current + 2); i++) {
        pages.push(i)
    }

    // Show last page
    if (current < total - 3) pages.push('...')
    if (current < total - 2) pages.push(total)

    return pages
})

// Methods
const loadProfiles = async () => {
    loading.value = true
    try {
        const params = {
            page: pagination.value.page,
            per_page: pagination.value.per_page,
            sort_by: sorting.value.sort_by,
            sort_order: sorting.value.sort_order,
            ...filters.value,
        }

        // Remove empty filters
        Object.keys(params).forEach(key => {
            if (params[key] === '') delete params[key]
        })

        const response = await api.get('/profiles/', {params})
        profiles.value = response.data.profiles
        pagination.value = {
            page: response.data.page,
            per_page: response.data.per_page,
            total: response.data.total,
            total_pages: response.data.total_pages,
        }
    } catch (error) {
        showNotification('Ошибка при загрузке профилей', 'error')
    } finally {
        loading.value = false
    }
}

const loadStats = async () => {
    try {
        const response = await api.get('/profiles/stats/summary')
        stats.value = response.data
    } catch (error) {
        console.error('Error loading stats:', error)
    }
}

const refreshProfiles = async () => {
    await Promise.all([loadProfiles(), loadStats()])
}

let searchTimeout: ReturnType<typeof setTimeout>
const debounceSearch = () => {
    clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => {
        pagination.value.page = 1
        loadProfiles()
    }, 500)
}

const applyFilters = () => {
    pagination.value.page = 1
    loadProfiles()
}

const sortBy = (column: string) => {
    if (sorting.value.sort_by === column) {
        sorting.value.sort_order = sorting.value.sort_order === 'asc' ? 'desc' : 'asc'
    } else {
        sorting.value.sort_by = column
        sorting.value.sort_order = 'asc'
    }
    loadProfiles()
}

const changePage = (page: number) => {
    if (page >= 1 && page <= pagination.value.total_pages) {
        pagination.value.page = page
        loadProfiles()
    }
}

const toggleSelectAll = () => {
    if (allSelected.value) {
        selectedProfiles.value = []
    } else {
        selectedProfiles.value = profiles.value.map(p => p.id)
    }
}

const toggleProfile = (profileId: string) => {
    const index = selectedProfiles.value.indexOf(profileId)
    if (index > -1) {
        selectedProfiles.value.splice(index, 1)
    } else {
        selectedProfiles.value.push(profileId)
    }
}

const selectProfile = (profileId: string, event?: Event) => {
    if (event && (event.target as HTMLElement).closest('input, button')) {
        return
    }
    openProfile(profileId)
}

const openProfile = (profileId: string) => {
    router.push(`/profiles/${profileId}`)
}

const confirmDeleteProfile = (profile: Profile) => {
    profileToDelete.value = profile
    showDeleteModal.value = true
}

const deleteProfile = async () => {
    if (!profileToDelete.value) return

    try {
        await api.delete(`/profiles/${profileToDelete.value.id}`)
        showNotification('Профиль успешно удален', 'success')
        showDeleteModal.value = false
        profileToDelete.value = null
        await refreshProfiles()
    } catch (error) {
        showNotification('Ошибка при удалении профиля', 'error')
    }
}

const bulkDeleteProfiles = async () => {
    try {
        await api.post('/profiles/bulk-delete', {
            profile_ids: selectedProfiles.value
        })
        showNotification(
            `Успешно удалено ${selectedProfiles.value.length} профилей`,
            'success'
        )
        showBulkDeleteModal.value = false
        selectedProfiles.value = []
        await refreshProfiles()
    } catch (error) {
        showNotification('Ошибка при массовом удалении', 'error')
    }
}

const getStatusClass = (profile: Profile) => {
    if (profile.corruption_reason) {
        return 'bg-red-100 text-red-800'
    }
    if (profile.is_warmed_up) {
        return 'bg-green-100 text-green-800'
    }
    return 'bg-yellow-100 text-yellow-800'
}

const getStatusText = (profile: Profile) => {
    if (profile.corruption_reason) {
        return 'Испорченный'
    }
    if (profile.is_warmed_up) {
        return 'Прогрет'
    }
    return 'Не прогрет'
}

const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(new Date(dateString))
}

const declension = (count: number, forms: string[]) => {
    const mod10 = count % 10
    const mod100 = count % 100

    if (mod100 >= 11 && mod100 <= 19) {
        return forms[2]
    }
    if (mod10 === 1) {
        return forms[0]
    }
    if (mod10 >= 2 && mod10 <= 4) {
        return forms[1]
    }
    return forms[2]
}

// Lifecycle
onMounted(() => {
    refreshProfiles()
})
</script>
