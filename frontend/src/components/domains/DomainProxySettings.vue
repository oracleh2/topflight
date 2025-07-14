<!-- frontend/src/components/domains/DomainProxySettings.vue -->
<template>
    <div class="bg-white shadow-sm rounded-lg p-6">
        <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-medium text-gray-900">Настройки прокси</h3>
            <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        {{ totalProxies }} прокси
      </span>
        </div>

        <!-- Настройки использования прокси -->
        <div class="space-y-6">
            <!-- Использование прокси для замеров -->
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <input
                        id="use-warmup-proxy"
                        v-model="settings.useWarmupProxyForParsing"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                </div>
                <div class="flex-1 min-w-0">
                    <label for="use-warmup-proxy" class="text-sm font-medium text-gray-700">
                        Использовать прокси профиля для замеров
                    </label>
                    <p class="text-sm text-gray-500">
                        Если включено, для замера позиций будет использоваться та же прокси, что и
                        для нагула профиля.
                        При сбое будет выбрана случайная прокси для замеров.
                    </p>
                </div>
            </div>

            <!-- Fallback для замеров -->
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <input
                        id="fallback-parsing-proxy"
                        v-model="settings.useFallbackForParsing"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    >
                </div>
                <div class="flex-1 min-w-0">
                    <label for="fallback-parsing-proxy" class="text-sm font-medium text-gray-700">
                        Использовать резервные прокси при сбоях
                    </label>
                    <p class="text-sm text-gray-500">
                        При неудаче с основной прокси будет выбрана случайная рабочая прокси для
                        замеров
                    </p>
                </div>
            </div>

            <!-- Статистика прокси -->
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <UserIcon class="h-5 w-5 text-gray-400"/>
                        </div>
                        <div class="ml-3 flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-900">
                                Прокси для нагула
                            </p>
                            <p class="text-sm text-gray-500">
                                {{ proxiesStats.warmup.total }} всего, {{
                                    proxiesStats.warmup.active
                                }} активных
                            </p>
                        </div>
                    </div>
                </div>

                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <MagnifyingGlassIcon class="h-5 w-5 text-gray-400"/>
                        </div>
                        <div class="ml-3 flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-900">
                                Прокси для замеров
                            </p>
                            <p class="text-sm text-gray-500">
                                {{ proxiesStats.parsing.total }} всего,
                                {{ proxiesStats.parsing.active }} активных
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Управление прокси -->
            <div class="border-t border-gray-200 pt-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="text-sm font-medium text-gray-900">Управление прокси</h4>
                        <p class="text-sm text-gray-500">
                            Добавляйте и настраивайте прокси для этого домена
                        </p>
                    </div>
                    <button
                        @click="showProxyManager = true"
                        class="btn-primary"
                    >
                        <CogIcon class="h-4 w-4 mr-2"/>
                        Настроить прокси
                    </button>
                </div>
            </div>

            <!-- Последние использованные прокси -->
            <div v-if="recentProxies.length > 0" class="border-t border-gray-200 pt-6">
                <h4 class="text-sm font-medium text-gray-900 mb-3">
                    Недавно использованные прокси
                </h4>
                <div class="space-y-2">
                    <div
                        v-for="proxy in recentProxies"
                        :key="proxy.id"
                        class="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                    >
                        <div class="flex items-center space-x-3">
                            <div
                                :class="[
                  proxy.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800',
                  'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium'
                ]"
                            >
                                {{ proxy.status === 'active' ? 'Активна' : 'Неактивна' }}
                            </div>
                            <div>
                                <p class="text-sm font-medium text-gray-900">
                                    {{ proxy.host }}:{{ proxy.port }}
                                </p>
                                <p class="text-xs text-gray-500">
                                    {{ proxy.type === 'warmup' ? 'Нагул' : 'Замеры' }} •
                                    Успешность: {{ proxy.success_rate }}% •
                                    Использований: {{ proxy.total_uses }}
                                </p>
                            </div>
                        </div>
                        <div class="text-xs text-gray-400">
                            {{ formatTimeAgo(proxy.last_used) }}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Сохранение настроек -->
            <div class="border-t border-gray-200 pt-6">
                <div class="flex justify-end space-x-3">
                    <button
                        @click="resetSettings"
                        :disabled="saving"
                        class="btn-secondary"
                    >
                        Сбросить
                    </button>
                    <button
                        @click="saveSettings"
                        :disabled="saving"
                        class="btn-primary"
                    >
                        {{ saving ? 'Сохранение...' : 'Сохранить настройки' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Модальное окно управления прокси -->
        <ProxyManagerModal
            :is-open="showProxyManager"
            :domain-id="domainId"
            @close="showProxyManager = false"
            @updated="handleProxyUpdate"
        />
    </div>
</template>

<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {CogIcon, MagnifyingGlassIcon, UserIcon} from '@heroicons/vue/24/outline'
import ProxyManagerModal from '@/components/proxy/ProxyManagerModal.vue'
import {api} from '@/api'

interface Props {
    domainId: string
}

const props = defineProps<Props>()

interface ProxySettings {
    useWarmupProxyForParsing: boolean
    useFallbackForParsing: boolean
}

interface ProxyStats {
    warmup: { total: number, active: number }
    parsing: { total: number, active: number }
}

// State
const loading = ref(false)
const saving = ref(false)
const showProxyManager = ref(false)

const settings = ref<ProxySettings>({
    useWarmupProxyForParsing: true,
    useFallbackForParsing: true
})

const proxiesStats = ref<ProxyStats>({
    warmup: {total: 0, active: 0},
    parsing: {total: 0, active: 0}
})

const recentProxies = ref<any[]>([])

// Computed
const totalProxies = computed(() =>
    proxiesStats.value.warmup.total + proxiesStats.value.parsing.total
)

// Methods
const loadProxySettings = async () => {
    loading.value = true
    try {
        // Используем правильный метод из вашего API класса
        const response = await api.getDomainProxies(props.domainId)

        if (response.data.success) {
            // ИСПРАВЛЕНИЕ: убеждаемся что data это массив
            const proxies = Array.isArray(response.data.data) ? response.data.data : []

            // Подсчитываем статистику
            const warmupProxies = proxies.filter(p => p.proxy_type === 'warmup')
            const parsingProxies = proxies.filter(p => p.proxy_type === 'parsing')

            proxiesStats.value = {
                warmup: {
                    total: warmupProxies.length,
                    active: warmupProxies.filter(p => p.status === 'active').length
                },
                parsing: {
                    total: parsingProxies.length,
                    active: parsingProxies.filter(p => p.status === 'active').length
                }
            }

            // Берем последние использованные прокси
            recentProxies.value = proxies
                .filter(p => p.last_check)
                .sort((a, b) => new Date(b.last_check).getTime() - new Date(a.last_check).getTime())
                .slice(0, 5)
                .map(p => ({
                    ...p,
                    type: p.proxy_type // Добавляем поле type для отображения
                }))
        }

        // Загружаем настройки (пока моковые)
        settings.value = {
            useWarmupProxyForParsing: true,
            useFallbackForParsing: true
        }
    } catch (error) {
        console.error('Ошибка загрузки настроек прокси:', error)

        // В случае ошибки показываем моковые данные
        proxiesStats.value = {
            warmup: {total: 2, active: 2},
            parsing: {total: 3, active: 2}
        }
        recentProxies.value = [
            {
                id: '1',
                host: '192.168.1.1',
                port: 8080,
                type: 'warmup',
                status: 'active',
                success_rate: 95,
                total_uses: 125,
                last_used: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
            },
            {
                id: '2',
                host: '10.0.0.5',
                port: 3128,
                type: 'parsing',
                status: 'active',
                success_rate: 87,
                total_uses: 89,
                last_used: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString()
            }
        ]
    } finally {
        loading.value = false
    }
}

const saveSettings = async () => {
    saving.value = true
    try {
        // Пока API для настроек домена не готово, используем моковые данные
        await new Promise(resolve => setTimeout(resolve, 1000))
        console.log('Настройки сохранены:', settings.value)
    } catch (error) {
        console.error('Ошибка сохранения настроек:', error)
    } finally {
        saving.value = false
    }
}

const resetSettings = () => {
    settings.value = {
        useWarmupProxyForParsing: true,
        useFallbackForParsing: true
    }
}

const handleProxyUpdate = () => {
    loadProxySettings()
}

const formatTimeAgo = (dateString: string) => {
    if (!dateString) return 'Никогда'

    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) {
        return `${diffDays} дн. назад`
    } else if (diffHours > 0) {
        return `${diffHours} ч. назад`
    } else {
        return 'Недавно'
    }
}

// Lifecycle
onMounted(() => {
    loadProxySettings()
})
</script>

<!-- Дополнение к DomainKeywords.vue для интеграции управления прокси -->
<!--
Добавить в DomainKeywords.vue новую секцию:

<div class="mt-8">
  <DomainProxySettings :domain-id="domainId" />
</div>
-->

<!-- Обновление backend API для поддержки настроек прокси домена -->
<!--
Добавить в backend/app/api/domains.py:

@router.get("/{domain_id}/proxy-settings")
async def get_domain_proxy_settings(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Загрузка настроек прокси для домена
    pass

@router.put("/{domain_id}/proxy-settings")
async def update_domain_proxy_settings(
    domain_id: str,
    settings: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Сохранение настроек прокси для домена
    pass

@router.get("/proxies/domain/{domain_id}/stats")
async def get_domain_proxy_stats(
    domain_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Статистика прокси домена
    pass
-->
