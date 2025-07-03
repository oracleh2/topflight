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

    <!-- Quick actions -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900">Быстрые действия</h3>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <router-link
            to="/domains"
            class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <div class="flex-shrink-0">
              <GlobeAltIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900">Добавить домен</p>
              <p class="text-sm text-gray-500 truncate">Начать отслеживание</p>
            </div>
          </router-link>

          <router-link
            to="/profile"
            class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <div class="flex-shrink-0">
              <UserIcon class="h-6 w-6 text-gray-400" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900">API ключ</p>
              <p class="text-sm text-gray-500 truncate">Настройки интеграции</p>
            </div>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Welcome message for new users -->
    <div v-if="!authStore.user?.domains_count" class="bg-blue-50 border border-blue-200 rounded-lg p-6">
      <div class="flex">
        <div class="flex-shrink-0">
          <GlobeAltIcon class="h-6 w-6 text-blue-600" aria-hidden="true" />
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-blue-800">
            Добро пожаловать в Yandex Parser!
          </h3>
          <div class="mt-2 text-sm text-blue-700">
            <p>
              Для начала работы добавьте домен для отслеживания позиций в поисковой выдаче Яндекса.
            </p>
          </div>
          <div class="mt-4">
            <div class="-mx-2 -my-1.5 flex">
              <router-link
                to="/domains"
                class="bg-blue-100 px-2 py-1.5 rounded-md text-sm font-medium text-blue-800 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-blue-50 focus:ring-blue-600"
              >
                Добавить домен
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent activity -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900">Последние задачи</h3>
      </div>
      <div class="divide-y divide-gray-200">
        <div
          v-if="recentTasks.length === 0"
          class="px-6 py-4 text-center text-gray-500"
        >
          <ClipboardDocumentListIcon class="mx-auto h-12 w-12 text-gray-300" />
          <h3 class="mt-2 text-sm font-medium text-gray-900">Задач пока нет</h3>
          <p class="mt-1 text-sm text-gray-500">
            Добавьте домены и ключевые слова для начала отслеживания
          </p>
        </div>
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
            <div class="flex-shrink-0">
              <span
                :class="[
                  'inline-flex px-2 py-1 text-xs font-medium rounded-full',
                  getTaskStatusClass(task.status)
                ]"
              >
                {{ getTaskStatusText(task.status) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  GlobeAltIcon,
  ClipboardDocumentListIcon,
  CurrencyDollarIcon,
  UserIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

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
    value: formatCurrency(authStore.user?.current_balance || authStore.user?.balance || 0),
    icon: CurrencyDollarIcon,
    href: '/billing',
    action: 'Пополнить баланс'
  },
  {
    name: 'Активные задачи',
    value: recentTasks.value.length,
    icon: ClipboardDocumentListIcon,
    href: '/tasks',
    action: 'Посмотреть все'
  }
])

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 2
  }).format(amount)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('ru-RU')
}

const getTaskDescription = (task: any) => {
  return `Задача ${task.task_type || 'неизвестна'}`
}

const getTaskStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'Ожидает',
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

onMounted(async () => {
  // Загружаем данные при монтировании
  if (authStore.isAuthenticated && !authStore.user) {
    try {
      await authStore.fetchProfile()
    } catch (error) {
      console.error('Ошибка загрузки профиля:', error)
    }
  }
})
</script>
