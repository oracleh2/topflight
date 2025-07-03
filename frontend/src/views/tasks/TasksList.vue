<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="sm:flex sm:items-center">
      <div class="sm:flex-auto">
        <h1 class="text-xl font-semibold text-gray-900">Задачи</h1>
        <p class="mt-2 text-sm text-gray-700">
          Отслеживайте статус выполнения ваших задач
        </p>
      </div>
      <div class="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
        <button
          type="button"
          class="btn-primary"
          @click="showQuickParseModal = true"
        >
          Быстрый парсинг
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex flex-wrap items-center gap-4">
          <div>
            <label for="statusFilter" class="block text-sm font-medium text-gray-700">
              Статус
            </label>
            <select
              id="statusFilter"
              v-model="filters.status"
              @change="applyFilters"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">Все статусы</option>
              <option value="pending">В очереди</option>
              <option value="running">Выполняется</option>
              <option value="completed">Завершено</option>
              <option value="failed">Ошибка</option>
            </select>
          </div>

          <div>
            <label for="typeFilter" class="block text-sm font-medium text-gray-700">
              Тип задачи
            </label>
            <select
              id="typeFilter"
              v-model="filters.type"
              @change="applyFilters"
              class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="">Все типы</option>
              <option value="parse_serp">Парсинг SERP</option>
              <option value="check_positions">Проверка позиций</option>
              <option value="warmup_profile">Прогрев профиля</option>
            </select>
          </div>

          <div class="flex items-end">
            <button
              @click="refreshTasks"
              class="btn-secondary"
              :disabled="tasksStore.loading"
            >
              <ArrowPathIcon class="mr-2 h-4 w-4" />
              Обновить
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="tasksStore.loading && !filteredTasks.length" class="flex justify-center py-12">
      <Spinner class="h-8 w-8 text-primary-600" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!filteredTasks.length"
      class="text-center py-12"
    >
      <ClipboardDocumentListIcon class="mx-auto h-12 w-12 text-gray-400" />
      <h3 class="mt-2 text-sm font-medium text-gray-900">
        {{ hasFilters ? 'Задач не найдено' : 'Нет задач' }}
      </h3>
      <p class="mt-1 text-sm text-gray-500">
        {{ hasFilters
          ? 'Попробуйте изменить фильтры или создать новую задачу'
          : 'Создайте первую задачу для начала работы'
        }}
      </p>
      <div v-if="!hasFilters" class="mt-6">
        <button
          type="button"
          class="btn-primary"
          @click="showQuickParseModal = true"
        >
          <PlusIcon class="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
          Создать задачу
        </button>
      </div>
    </div>

    <!-- Tasks list -->
    <div v-else class="bg-white shadow overflow-hidden sm:rounded-md">
      <ul role="list" class="divide-y divide-gray-200">
        <li
          v-for="task in filteredTasks"
          :key="task.task_id"
          class="px-6 py-4 hover:bg-gray-50"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center min-w-0 flex-1">
              <div class="flex-shrink-0">
                <div
                  :class="[
                    'h-10 w-10 rounded-lg flex items-center justify-center',
                    getTaskStatusBg(task.status)
                  ]"
                >
                  <component
                    :is="getTaskIcon(task.task_type)"
                    :class="[
                      'h-6 w-6',
                      getTaskStatusColor(task.status)
                    ]"
                  />
                </div>
              </div>

              <div class="ml-4 min-w-0 flex-1">
                <div class="flex items-center">
                  <p class="text-sm font-medium text-gray-900 truncate">
                    {{ getTaskTitle(task) }}
                  </p>
                  <span
                    :class="[
                      'ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                      getTaskStatusClass(task.status)
                    ]"
                  >
                    {{ getTaskStatusText(task.status) }}
                  </span>
                </div>

                <div class="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                  <span>{{ getTaskTypeText(task.task_type) }}</span>
                  <span>•</span>
                  <span>{{ formatDateTime(task.created_at) }}</span>
                  <span v-if="task.completed_at">•</span>
                  <span v-if="task.completed_at">
                    Завершено {{ formatDateTime(task.completed_at) }}
                  </span>
                </div>

                <!-- Task details -->
                <div v-if="task.parameters" class="mt-2 text-sm text-gray-600">
                  <div v-if="task.task_type === 'parse_serp'" class="flex items-center space-x-4">
                    <span>Страниц: {{ task.parameters.pages || 10 }}</span>
                    <span>•</span>
                    <span>Регион: {{ task.parameters.region_code || '213' }}</span>
                    <span>•</span>
                    <span>Устройство: {{ task.parameters.device_type || 'desktop' }}</span>
                  </div>
                  <div v-else-if="task.task_type === 'check_positions'" class="flex items-center space-x-4">
                    <span>Ключевых слов: {{ task.parameters.keyword_ids?.length || 0 }}</span>
                    <span>•</span>
                    <span>Устройство: {{ task.parameters.device_type || 'desktop' }}</span>
                  </div>
                </div>

                <!-- Error message -->
                <div v-if="task.error_message" class="mt-2">
                  <Alert
                    type="error"
                    :message="task.error_message"
                    class="text-sm"
                  />
                </div>

                <!-- Results preview -->
                <div v-if="task.result && task.status === 'completed'" class="mt-2 text-sm text-gray-600">
                  <div v-if="task.task_type === 'parse_serp'">
                    Найдено результатов: {{ task.result.results_count || 0 }}
                  </div>
                  <div v-else-if="task.task_type === 'check_positions'">
                    Проверено: {{ task.result.checked_keywords || 0 }} ключевых слов
                  </div>
                </div>
              </div>
            </div>

            <div class="ml-4 flex items-center space-x-2">
              <button
                v-if="task.status === 'completed' && task.result"
                @click="viewTaskResults(task)"
                class="btn-secondary text-sm"
              >
                Результаты
              </button>

              <Menu as="div" class="relative">
                <MenuButton class="p-2 rounded-md text-gray-400 hover:text-gray-600">
                  <EllipsisVerticalIcon class="h-5 w-5" />
                </MenuButton>

                <transition
                  enter-active-class="transition ease-out duration-100"
                  enter-from-class="transform opacity-0 scale-95"
                  enter-to-class="transform opacity-100 scale-100"
                  leave-active-class="transition ease-in duration-75"
                  leave-from-class="transform opacity-100 scale-100"
                  leave-to-class="transform opacity-0 scale-95"
                >
                  <MenuItems class="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <MenuItem v-slot="{ active }">
                      <button
                        @click="refreshTaskStatus(task)"
                        :class="[
                          active ? 'bg-gray-100' : '',
                          'block w-full text-left px-4 py-2 text-sm text-gray-700'
                        ]"
                      >
                        Обновить статус
                      </button>
                    </MenuItem>

                    <MenuItem v-if="task.task_type === 'parse_serp' && task.status === 'completed'" v-slot="{ active }">
                      <button
                        @click="createSimilarTask(task)"
                        :class="[
                          active ? 'bg-gray-100' : '',
                          'block w-full text-left px-4 py-2 text-sm text-gray-700'
                        ]"
                      >
                        Повторить задачу
                      </button>
                    </MenuItem>
                  </MenuItems>
                </transition>
              </Menu>
            </div>
          </div>
        </li>
      </ul>

      <!-- Load more -->
      <div v-if="canLoadMore" class="px-6 py-4 text-center border-t border-gray-200">
        <button
          @click="loadMoreTasks"
          class="btn-secondary"
          :disabled="tasksStore.loading"
        >
          <Spinner v-if="tasksStore.loading" class="mr-2 h-4 w-4" />
          Загрузить еще
        </button>
      </div>
    </div>

    <!-- Quick parse modal -->
    <QuickParseModal
      :isOpen="showQuickParseModal"
      @close="showQuickParseModal = false"
      @success="handleTaskCreated"
    />

    <!-- Task results modal -->
    <TaskResultsModal
      :isOpen="showResultsModal"
      :task="selectedTask"
      @close="showResultsModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import {
  ClipboardDocumentListIcon,
  PlusIcon,
  ArrowPathIcon,
  EllipsisVerticalIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon,
  CogIcon,
} from '@heroicons/vue/24/outline'
import { useTasksStore, type Task } from '@/stores/tasks'
import Spinner from '@/components/ui/Spinner.vue'
import Alert from '@/components/ui/Alert.vue'
import QuickParseModal from '@/components/modals/QuickParseModal.vue'
import TaskResultsModal from '@/components/modals/TaskResultsModal.vue'

const tasksStore = useTasksStore()

const showQuickParseModal = ref(false)
const showResultsModal = ref(false)
const selectedTask = ref<Task | null>(null)
const currentPage = ref(0)
const pageSize = 20

const filters = reactive({
  status: '',
  type: ''
})

const filteredTasks = computed(() => {
  let tasks = tasksStore.tasks

  if (filters.status) {
    tasks = tasks.filter(task => task.status === filters.status)
  }

  if (filters.type) {
    tasks = tasks.filter(task => task.task_type === filters.type)
  }

  return tasks
})

const hasFilters = computed(() => {
  return filters.status || filters.type
})

const canLoadMore = computed(() => {
  return tasksStore.tasks.length >= (currentPage.value + 1) * pageSize
})

const formatDateTime = (dateString: string) => {
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(dateString))
}

const getTaskIcon = (taskType: string) => {
  const iconMap: Record<string, any> = {
    parse_serp: MagnifyingGlassIcon,
    check_positions: CheckCircleIcon,
    warmup_profile: CogIcon
  }
  return iconMap[taskType] || ClipboardDocumentListIcon
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

const getTaskStatusBg = (status: string) => {
  const bgMap: Record<string, string> = {
    pending: 'bg-yellow-100',
    running: 'bg-blue-100',
    completed: 'bg-green-100',
    failed: 'bg-red-100'
  }
  return bgMap[status] || 'bg-gray-100'
}

const getTaskStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'text-yellow-600',
    running: 'text-blue-600',
    completed: 'text-green-600',
    failed: 'text-red-600'
  }
  return colorMap[status] || 'text-gray-600'
}

const getTaskTypeText = (taskType: string) => {
  const typeMap: Record<string, string> = {
    parse_serp: 'Парсинг SERP',
    check_positions: 'Проверка позиций',
    warmup_profile: 'Прогрев профиля'
  }
  return typeMap[taskType] || taskType
}

const getTaskTitle = (task: Task) => {
  if (task.task_type === 'parse_serp') {
    return `Парсинг: ${task.parameters?.keyword || 'неизвестный запрос'}`
  } else if (task.task_type === 'check_positions') {
    return `Проверка позиций: ${task.parameters?.keyword_ids?.length || 0} ключевых слов`
  } else if (task.task_type === 'warmup_profile') {
    return 'Прогрев профиля'
  }
  return task.task_type
}

const applyFilters = () => {
  // Фильтрация происходит автоматически через computed свойство
}

const refreshTasks = async () => {
  currentPage.value = 0
  try {
    await tasksStore.fetchUserTasks(pageSize, 0)
  } catch (error) {
    console.error('Error refreshing tasks:', error)
  }
}

const loadMoreTasks = async () => {
  currentPage.value += 1
  try {
    await tasksStore.fetchUserTasks(pageSize, currentPage.value * pageSize)
  } catch (error) {
    console.error('Error loading more tasks:', error)
    currentPage.value -= 1
  }
}

const refreshTaskStatus = async (task: Task) => {
  try {
    const updatedTask = await tasksStore.getTaskStatus(task.task_id)
    // Обновляем задачу в списке
    const index = tasksStore.tasks.findIndex(t => t.task_id === task.task_id)
    if (index !== -1) {
      tasksStore.tasks[index] = { ...task, ...updatedTask }
    }
  } catch (error) {
    console.error('Error refreshing task status:', error)
  }
}

const viewTaskResults = (task: Task) => {
  selectedTask.value = task
  showResultsModal.value = true
}

const createSimilarTask = (task: Task) => {
  // Логика создания похожей задачи
  if (task.task_type === 'parse_serp' && task.parameters) {
    showQuickParseModal.value = true
    // Можно передать параметры в модальное окно для предзаполнения
  }
}

const handleTaskCreated = () => {
  showQuickParseModal.value = false
  refreshTasks()
}

onMounted(() => {
  refreshTasks()
})
</script>
