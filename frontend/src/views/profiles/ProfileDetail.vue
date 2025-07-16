<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center justify-between">
            <div class="flex items-center">
                <button
                    @click="goBack"
                    class="mr-4 p-2 hover:bg-gray-100 rounded-full"
                >
                    <ArrowLeftIcon class="h-5 w-5 text-gray-600"/>
                </button>
                <div>
                    <h1 class="text-xl font-semibold text-gray-900">
                        {{ profile?.name || 'Профиль' }}
                    </h1>
                    <p class="text-sm text-gray-500">
                        ID: {{ profile?.id }}
                    </p>
                </div>
            </div>
            <div class="flex space-x-3">
                <button
                    @click="refreshProfile"
                    class="btn-secondary"
                    :disabled="loading"
                >
                    <ArrowPathIcon class="h-4 w-4 mr-2" :class="{ 'animate-spin': loading }"/>
                    Обновить
                </button>
                <button
                    @click="confirmDelete"
                    class="btn-danger"
                >
                    <TrashIcon class="h-4 w-4 mr-2"/>
                    Удалить
                </button>
            </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
            <ArrowPathIcon class="h-8 w-8 animate-spin text-gray-400"/>
            <span class="ml-2 text-gray-500">Загрузка...</span>
        </div>

        <!-- Profile Content -->
        <div v-else-if="profile" class="space-y-6">
            <!-- Status Badge -->
            <div class="flex items-center space-x-4">
        <span :class="[
          'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
          getStatusClass(profile)
        ]">
          {{ getStatusText(profile) }}
        </span>
                <div class="flex items-center text-sm text-gray-500">
                    <ComputerDesktopIcon v-if="profile.device_type === 'desktop'"
                                         class="h-5 w-5 mr-2"/>
                    <DevicePhoneMobileIcon v-else-if="profile.device_type === 'mobile'"
                                           class="h-5 w-5 mr-2"/>
                    <DeviceTabletIcon v-else class="h-5 w-5 mr-2"/>
                    <span class="capitalize">{{ profile.device_type }}</span>
                </div>
            </div>

            <!-- Main Info Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Basic Information -->
                <div class="lg:col-span-2">
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-6 py-4 border-b border-gray-200">
                            <h3 class="text-lg font-medium text-gray-900">Основная информация</h3>
                        </div>
                        <div class="px-6 py-4">
                            <dl class="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2">
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Название</dt>
                                    <dd class="mt-1 text-sm text-gray-900">{{ profile.name }}</dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Тип устройства
                                    </dt>
                                    <dd class="mt-1 text-sm text-gray-900 capitalize">
                                        {{ profile.device_type }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Дата создания</dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{ formatDate(profile.created_at) }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Последнее
                                        обновление
                                    </dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{ formatDate(profile.updated_at) }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Статус прогрева
                                    </dt>
                                    <dd class="mt-1">
                    <span :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      profile.is_warmed_up ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    ]">
                      {{ profile.is_warmed_up ? 'Прогрет' : 'Не прогрет' }}
                    </span>
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Последнее
                                        использование
                                    </dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{
                                            profile.last_used ? formatDate(profile.last_used) : 'Никогда'
                                        }}
                                    </dd>
                                </div>
                                <div class="sm:col-span-2">
                                    <dt class="text-sm font-medium text-gray-500">User Agent</dt>
                                    <dd class="mt-1 text-sm text-gray-900 break-all">
                                        {{ profile.user_agent }}
                                    </dd>
                                </div>
                            </dl>
                        </div>
                    </div>
                </div>

                <!-- Statistics -->
                <div class="space-y-6">
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-6 py-4 border-b border-gray-200">
                            <h3 class="text-lg font-medium text-gray-900">Статистика</h3>
                        </div>
                        <div class="px-6 py-4">
                            <dl class="space-y-4">
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Количество кук
                                    </dt>
                                    <dd class="mt-1 text-2xl font-semibold text-gray-900">
                                        {{ profile.cookies_count }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Посещенных
                                        сайтов
                                    </dt>
                                    <dd class="mt-1 text-2xl font-semibold text-gray-900">
                                        {{ profile.visited_sites_count }}
                                    </dd>
                                </div>
                            </dl>
                        </div>
                    </div>

                    <!-- Proxy Information -->
                    <div v-if="profile.proxy_info" class="bg-white shadow rounded-lg">
                        <div class="px-6 py-4 border-b border-gray-200">
                            <h3 class="text-lg font-medium text-gray-900">Прокси</h3>
                        </div>
                        <div class="px-6 py-4">
                            <dl class="space-y-3">
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Хост</dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{ profile.proxy_info.host }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Порт</dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{ profile.proxy_info.port }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Тип</dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{ profile.proxy_info.proxy_type }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Статус</dt>
                                    <dd class="mt-1">
                    <span :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      profile.proxy_info.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    ]">
                      {{ profile.proxy_info.is_active ? 'Активен' : 'Неактивен' }}
                    </span>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                    </div>

                    <!-- No Proxy State -->
                    <div v-else class="bg-white shadow rounded-lg">
                        <div class="px-6 py-4 border-b border-gray-200">
                            <h3 class="text-lg font-medium text-gray-900">Прокси</h3>
                        </div>
                        <div class="px-6 py-4">
                            <p class="text-sm text-gray-500">Прокси не назначен</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Browser Settings -->
            <div class="bg-white shadow rounded-lg">
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-medium text-gray-900">Настройки браузера</h3>
                </div>
                <div class="px-6 py-4">
                    <div class="bg-gray-50 rounded-md p-4">
                        <pre class="text-sm text-gray-600 overflow-x-auto">{{
                                JSON.stringify(profile.browser_settings, null, 2)
                            }}</pre>
                    </div>
                </div>
            </div>

            <!-- Fingerprint Information -->
            <div v-if="profile.fingerprint" class="bg-white shadow rounded-lg">
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-medium text-gray-900">Fingerprint</h3>
                </div>
                <div class="px-6 py-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <!-- Screen & Display -->
                        <div>
                            <h4 class="text-sm font-medium text-gray-900 mb-3">Экран и дисплей</h4>
                            <dl class="space-y-2">
                                <div>
                                    <dt class="text-xs text-gray-500">Разрешение экрана</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.screen_resolution || 'Не задано' }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Размер viewport</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.viewport_size || 'Не задано' }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Глубина цвета</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.color_depth || 'Не задано' }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Pixel ratio</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.pixel_ratio || 'Не задано' }}
                                    </dd>
                                </div>
                            </dl>
                        </div>

                        <!-- System Information -->
                        <div>
                            <h4 class="text-sm font-medium text-gray-900 mb-3">Системная
                                информация</h4>
                            <dl class="space-y-2">
                                <div>
                                    <dt class="text-xs text-gray-500">Платформа</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.platform || 'Не задано' }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Язык</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.language || 'Не задано' }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Часовой пояс</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.timezone || 'Не задано' }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Ядра CPU</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.cpu_cores || 'Не задано' }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Память (MB)</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.memory_size || 'Не задано' }}
                                    </dd>
                                </div>
                            </dl>
                        </div>

                        <!-- Security & Detection -->
                        <div>
                            <h4 class="text-sm font-medium text-gray-900 mb-3">Безопасность</h4>
                            <dl class="space-y-2">
                                <div>
                                    <dt class="text-xs text-gray-500">WebDriver обнаружен</dt>
                                    <dd class="text-sm">
                    <span :class="[
                      'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                      profile.fingerprint.webdriver_present ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    ]">
                      {{ profile.fingerprint.webdriver_present ? 'Да' : 'Нет' }}
                    </span>
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Автоматизация обнаружена</dt>
                                    <dd class="text-sm">
                    <span :class="[
                      'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                      profile.fingerprint.automation_detected ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    ]">
                      {{ profile.fingerprint.automation_detected ? 'Да' : 'Нет' }}
                    </span>
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-xs text-gray-500">Тип подключения</dt>
                                    <dd class="text-sm text-gray-900">
                                        {{ profile.fingerprint.connection_type || 'Не задано' }}
                                    </dd>
                                </div>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Lifecycle Information -->
            <div v-if="profile.lifecycle" class="bg-white shadow rounded-lg">
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-medium text-gray-900">Жизненный цикл</h3>
                </div>
                <div class="px-6 py-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <dl class="space-y-4">
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Количество
                                        использований
                                    </dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{ profile.lifecycle.current_usage_count || 0 }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Стадия каскада
                                    </dt>
                                    <dd class="mt-1">
                    <span :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      getCascadeStageClass(profile.lifecycle.cascade_stage)
                    ]">
                      {{ getCascadeStageText(profile.lifecycle.cascade_stage) }}
                    </span>
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Состояние</dt>
                                    <dd class="mt-1">
                    <span :class="[
                      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      profile.lifecycle.is_corrupted ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    ]">
                      {{ profile.lifecycle.is_corrupted ? 'Испорчен' : 'Исправен' }}
                    </span>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                        <div>
                            <dl class="space-y-4">
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Последняя
                                        проверка
                                    </dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{
                                            profile.lifecycle.last_health_check ? formatDate(profile.lifecycle.last_health_check) : 'Никогда'
                                        }}
                                    </dd>
                                </div>
                                <div>
                                    <dt class="text-sm font-medium text-gray-500">Следующая
                                        проверка
                                    </dt>
                                    <dd class="mt-1 text-sm text-gray-900">
                                        {{
                                            profile.lifecycle.next_health_check ? formatDate(profile.lifecycle.next_health_check) : 'Не запланирована'
                                        }}
                                    </dd>
                                </div>
                                <div v-if="profile.lifecycle.corruption_reason">
                                    <dt class="text-sm font-medium text-gray-500">Причина порчи</dt>
                                    <dd class="mt-1 text-sm text-red-600">
                                        {{ profile.lifecycle.corruption_reason }}
                                    </dd>
                                </div>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Error State -->
        <div v-else-if="!loading" class="text-center py-12">
            <ExclamationTriangleIcon class="mx-auto h-12 w-12 text-gray-400"/>
            <h3 class="mt-2 text-sm font-medium text-gray-900">Профиль не найден</h3>
            <p class="mt-1 text-sm text-gray-500">Профиль может быть удален или ID указан
                неверно</p>
            <div class="mt-6">
                <button @click="goBack" class="btn-primary">
                    Вернуться к списку
                </button>
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
                            Вы уверены, что хотите удалить профиль "{{ profile?.name }}"?
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
    </div>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useNotifications} from '@/composables/useNotifications'
import {api} from '@/api'
import {
    ArrowLeftIcon,
    ArrowPathIcon,
    TrashIcon,
    ComputerDesktopIcon,
    DevicePhoneMobileIcon,
    DeviceTabletIcon,
    ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline'

// Types
interface ProfileDetail {
    id: string
    name: string
    device_type: string
    created_at: string
    updated_at: string
    user_agent: string
    browser_settings: Record<string, any>
    cookies_count: number
    visited_sites_count: number
    is_warmed_up: boolean
    status: string
    last_used: string | null
    fingerprint: {
        user_agent: string
        screen_resolution: string
        viewport_size: string
        timezone: string
        language: string
        platform: string
        cpu_cores: number
        memory_size: number
        color_depth: number
        pixel_ratio: number
        webdriver_present: boolean
        automation_detected: boolean
        connection_type: string
    } | null
    lifecycle: {
        current_usage_count: number
        cascade_stage: number
        is_corrupted: boolean
        corruption_reason: string | null
        last_health_check: string | null
        next_health_check: string | null
    } | null
    proxy_info: {
        host: string
        port: number
        proxy_type: string
        is_active: boolean
    } | null
}

// Composables
const route = useRoute()
const router = useRouter()
const {showNotification} = useNotifications()

// Reactive state
const profile = ref<ProfileDetail | null>(null)
const loading = ref(false)
const showDeleteModal = ref(false)

// Methods
const loadProfile = async () => {
    const profileId = route.params.id as string
    loading.value = true

    try {
        const response = await api.get(`/profiles/${profileId}`)
        profile.value = response.data
    } catch (error) {
        if (error.response?.status === 404) {
            showNotification('Профиль не найден', 'error')
        } else {
            showNotification('Ошибка при загрузке профиля', 'error')
        }
    } finally {
        loading.value = false
    }
}

const refreshProfile = async () => {
    await loadProfile()
}

const goBack = () => {
    router.push('/profiles')
}

const confirmDelete = () => {
    showDeleteModal.value = true
}

const deleteProfile = async () => {
    if (!profile.value) return

    try {
        await api.delete(`/profiles/${profile.value.id}`)
        showNotification('Профиль успешно удален', 'success')
        router.push('/profiles')
    } catch (error) {
        showNotification('Ошибка при удалении профиля', 'error')
    }

    showDeleteModal.value = false
}

const getStatusClass = (profile: ProfileDetail) => {
    if (profile.lifecycle?.is_corrupted) {
        return 'bg-red-100 text-red-800'
    }
    if (profile.is_warmed_up) {
        return 'bg-green-100 text-green-800'
    }
    return 'bg-yellow-100 text-yellow-800'
}

const getStatusText = (profile: ProfileDetail) => {
    if (profile.lifecycle?.is_corrupted) {
        return 'Испорченный'
    }
    if (profile.is_warmed_up) {
        return 'Прогрет'
    }
    return 'Не прогрет'
}

const getCascadeStageClass = (stage: number) => {
    switch (stage) {
        case 0:
            return 'bg-blue-100 text-blue-800'
        case 1:
            return 'bg-yellow-100 text-yellow-800'
        case 2:
            return 'bg-orange-100 text-orange-800'
        case 3:
            return 'bg-green-100 text-green-800'
        default:
            return 'bg-gray-100 text-gray-800'
    }
}

const getCascadeStageText = (stage: number) => {
    switch (stage) {
        case 0:
            return 'Свежий'
        case 1:
            return 'Использованный'
        case 2:
            return 'Догуливание'
        case 3:
            return 'Готов повторно'
        default:
            return 'Неизвестно'
    }
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

// Lifecycle
onMounted(() => {
    loadProfile()
})
</script>
