<template>
  <div class="space-y-6">
    <!-- Stats cards -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <div
        v-for="stat in stats"
        :key="stat.name"
        class="bg-white overflow-hidden shadow rounded-lg"
      >
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <component
                :is="stat.icon"
                class="h-6 w-6 text-gray-400"
                aria-hidden="true"
              />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">
                  {{ stat.name }}
                </dt>
                <dd>
                  <div class="text-lg font-medium text-gray-900">
                    {{ stat.value }}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
        <div class="bg-gray-50 px-5 py-3">
          <div class="text-sm">
            <router-link
              :to="stat.href"
              class="font-medium text-primary-700 hover:text-primary-900"
            >
              {{ stat.action }}
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent tasks -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Последние задачи</h3>
        </div>
        <div class="divide-y divide-gray-200">
          <div
            v-for="task in recentTasks"
            :key="task.task_id"
            class="px-6 py-4 hover:bg-gray-50"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">
                  {{ getTaskDescription(task) }}
                </p>
                <p class="text-sm text-gray-500">
                  {{ formatDate(task.created_at) }}
                </p>
              </div>
              <div class="ml-4 flex-shrink-0">
                <span
                  :class="[
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    getTaskStatusClass(task.status)
                  ]"
                >
                  {{ getTaskStatusText(task.status) }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="!recentTasks.length" class="px-6 py-8 text-center">
            <p class="text-gray-500">Задач пока нет</p>
          </div>
        </div>
        <div class="bg-gray-50 px-6 py-3">
          <router-link
            to="/tasks"
            class="text-sm font-medium text-primary-700 hover:text-primary-900"
          >
            Все задачи →
          </router-link>
        </div>
      </div>

      <!-- Balance and billing -->
      <div class="bg-white shadow rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Баланс и биллинг</h3>
        </div>
        <div class="p-6">
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">Доступный баланс</span>
              <span class="text-lg font-semibold text-gray-900">
                {{ formatCurrency(billingStore.balance?.available_balance || 0) }}
              </span>
            </div>

            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">Зарезервировано</span>
              <span class="text-sm text-gray-600">
                {{ formatCurrency(billingStore.balance?.reserved_balance || 0) }}
              </span>
            </div>

            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">Текущий тариф</span>
              <span class="text-sm text-gray-900 font-medium">
                {{ billingStore.currentTariff?.name || 'Базовый' }}
              </span>
            </div>

            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">Стоимость проверки</span>
              <span class="text-sm text-gray-900">
                {{ formatCurrency(billingStore.currentTariff?.cost_per_check || 1) }}
              </span>
            </div>
          </div>

          <div class="mt-6">
            <router-link
              to="/billing"
              class="btn-primary w-full text-center"
            >
              Пополнить баланс
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick actions -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900">Быстрые действия</h3>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <router-link
            to="/domains"
            class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <div class="flex-shrink-0">
              <GlobeAltIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="flex-1 min-w-0">
              <span class="absolute inset-0" aria-hidden="true" />
              <p class="text-sm font-medium text-gray-900">Добавить домен</p>
              <p class="text-sm text-gray-500 truncate">Начните отслеживать новый сайт</p>
            </div>
          </router-link>

          <button
            @click="showParseModal = true"
            class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <div class="flex-shrink-0">
              <MagnifyingGlassIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900">Парсить выдачу</p>
              <p class="text-sm text-gray-500 truncate">Быстрый парсинг по запросу</p>
            </div>
          </button>

          <router-link
            to="/profile"
            class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <div class="flex-shrink-0">
              <UserIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="flex-1 min-w-0">
              <span class="absolute inset-0" aria-hidden="true" />
              <p class="text-sm font-medium text-gray-900">API ключ</p>
              <p class="text-sm text-gray-500 truncate">Настройки интеграции</p>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Quick parse modal -->
    <QuickParseModal
      :isOpen="showParseModal"
      @close="showParseModal = false"
      @success="handleParseSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  GlobeAltIcon,
  ClipboardDocumentListIcon,
  CurrencyRubleIcon,
  UserIcon,
  MagnifyingGlassIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useDomainsStore } from '@/stores/domains'
import { useBillingStore } from '@/stores/billing'
import { useTasksStore } from '@/stores/tasks'
import QuickParseModal from '@/components/modals/QuickParseModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const domainsStore = useDomainsStore()
const billingStore = useBillingStore()
const tasksStore = useTasksStore()

const showParseModal = ref(false)
const recentTasks = ref([])

const stats = computed(() => [
  {
    name: 'Домены',
    value: authStore.user?.domains_count || 0,
    icon: GlobeAltIcon,
    href: '/domains',
    action: 'Управлять доменами'
  },
  {
    name: 'Ключевые слова',
    value: authStore.user?.keywords_count || 0,
    icon: ClipboardDocumentListIcon,
    href: '/domains',
    action: 'Добавить слова'
  },
  {
    name: 'Баланс',
    value: formatCurrency(authStore.availableBalance),
    icon: CurrencyRubleIcon,
    href: '/billing',
    action: 'Пополнить'
  },
  {
    name: 'Тариф',
    value: billingStore.currentTariff?.name || 'Базовый',
    icon: UserIcon,
    href: '/billing',
    action: 'Изменить тариф'
  }
])

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

const formatDate = (dateString: string) => {
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(dateString))
}

const getTaskDescription = (task: any) => {
  if (task.task_type === 'parse_serp') {
    return `Парсинг: ${task.parameters?.keyword || 'неизвестный запрос'}`
  } else if (task.task_type === 'check_positions') {
    return `Проверка позиций: ${task.parameters?.keyword_ids?.length || 0} слов`
  } else if (task.task_type === 'warmup_profile') {
    return 'Прогрев профиля'
  }
  return task.task_type
}

const getTaskStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'В очереди',
    running: 'Выполняется',
    completed: 'Завершено',
    failed: 'Ошибка'
  }
  return statusMap[status] || status
}

const getTaskStatusClass = (status: string) => {
  const classMap: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800'
  }
  return classMap[status] || 'bg-gray-100 text-gray-800'
}

const handleParseSuccess = (taskId: string) => {
  showParseModal.value = false
  router.push(`/tasks`)
}

onMounted(async () => {
  try {
    await Promise.all([
      billingStore.fetchBalance(),
      billingStore.fetchCurrentTariff(),
      // Загружаем последние задачи
      tasksStore.fetchUserTasks(10, 0)
    ])

    recentTasks.value = tasksStore.tasks.slice(0, 5)
  } catch (error) {
    console.error('Error loading dashboard data:', error)
  }
})
</script>
