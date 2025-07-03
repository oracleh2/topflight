<template>
  <Modal
    :isOpen="isOpen"
    title="Результаты задачи"
    panel-class="max-w-6xl"
    @close="$emit('close')"
  >
    <div v-if="task" class="space-y-6">
      <!-- Task info -->
      <div class="bg-gray-50 rounded-lg p-4">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-gray-500">Тип задачи:</span>
            <div class="font-medium">{{ getTaskTypeText(task.task_type) }}</div>
          </div>
          <div>
            <span class="text-gray-500">Статус:</span>
            <div>
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
          <div>
            <span class="text-gray-500">Создано:</span>
            <div class="font-medium">{{ formatDateTime(task.created_at) }}</div>
          </div>
          <div v-if="task.completed_at">
            <span class="text-gray-500">Завершено:</span>
            <div class="font-medium">{{ formatDateTime(task.completed_at) }}</div>
          </div>
        </div>
      </div>

      <!-- Task parameters -->
      <div v-if="task.parameters">
        <h3 class="text-lg font-medium text-gray-900 mb-3">Параметры задачи</h3>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div v-if="task.parameters.keyword">
              <span class="text-gray-500">Ключевое слово:</span>
              <div class="font-medium">{{ task.parameters.keyword }}</div>
            </div>
            <div v-if="task.parameters.device_type">
              <span class="text-gray-500">Устройство:</span>
              <div class="font-medium">
                {{ task.parameters.device_type === 'desktop' ? 'Десктоп' : 'Мобильный' }}
              </div>
            </div>
            <div v-if="task.parameters.pages">
              <span class="text-gray-500">Страниц:</span>
              <div class="font-medium">{{ task.parameters.pages }}</div>
            </div>
            <div v-if="task.parameters.region_code">
              <span class="text-gray-500">Регион:</span>
              <div class="font-medium">{{ task.parameters.region_code }}</div>
            </div>
            <div v-if="task.parameters.keyword_ids">
              <span class="text-gray-500">Ключевых слов:</span>
              <div class="font-medium">{{ task.parameters.keyword_ids.length }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Results -->
      <div v-if="task.result">
        <h3 class="text-lg font-medium text-gray-900 mb-3">Результаты</h3>

        <!-- Parse results summary -->
        <div v-if="task.task_type === 'parse_serp'" class="space-y-4">
          <div class="bg-green-50 rounded-lg p-4">
            <div class="flex items-center">
              <CheckCircleIcon class="h-6 w-6 text-green-600 mr-2" />
              <div>
                <p class="font-medium text-green-900">
                  Найдено {{ task.result.results_count || 0 }} результатов
                </p>
                <p class="text-sm text-green-700">
                  Парсинг выполнен для запроса "{{ task.result.keyword }}"
                </p>
              </div>
            </div>
          </div>

          <div class="text-center">
            <button
              @click="downloadResults"
              class="btn-primary"
            >
              <ArrowDownTrayIcon class="mr-2 h-4 w-4" />
              Скачать результаты (CSV)
            </button>
          </div>
        </div>

        <!-- Position check results -->
        <div v-else-if="task.task_type === 'check_positions'" class="space-y-4">
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="flex items-center">
              <CheckCircleIcon class="h-6 w-6 text-blue-600 mr-2" />
              <div>
                <p class="font-medium text-blue-900">
                  Проверено {{ task.result.checked_keywords || 0 }} ключевых слов
                </p>
                <p class="text-sm text-blue-700">
                  Результаты проверки позиций готовы
                </p>
              </div>
            </div>
          </div>

          <!-- Results table -->
          <div v-if="task.result.results" class="bg-white border rounded-lg overflow-hidden">
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Ключевое слово
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Домен
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Позиция
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                  <tr
                    v-for="result in task.result.results"
                    :key="result.keyword_id"
                    class="hover:bg-gray-50"
                  >
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {{ result.keyword }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {{ result.domain }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span
                        v-if="result.position"
                        :class="[
                          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                          result.position <= 3 ? 'bg-green-100 text-green-800' :
                          result.position <= 10 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        ]"
                      >
                        {{ result.position }}
                      </span>
                      <span v-else class="text-sm text-gray-400">
                        Не найдено
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Profile warmup results -->
        <div v-else-if="task.task_type === 'warmup_profile'" class="space-y-4">
          <div class="bg-purple-50 rounded-lg p-4">
            <div class="flex items-center">
              <CogIcon class="h-6 w-6 text-purple-600 mr-2" />
              <div>
                <p class="font-medium text-purple-900">
                  {{ task.result.success ? 'Профиль успешно прогрет' : 'Ошибка прогрева профиля' }}
                </p>
                <p class="text-sm text-purple-700">
                  Посещено сайтов: {{ task.result.warmup_sites_visited || 0 }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error message -->
      <div v-if="task.error_message">
        <h3 class="text-lg font-medium text-gray-900 mb-3">Ошибка</h3>
        <Alert
          type="error"
          :message="task.error_message"
        />
      </div>
    </div>

    <template #actions>
      <button
        type="button"
        class="btn-primary"
        @click="$emit('close')"
      >
        Закрыть
      </button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { CheckCircleIcon, ArrowDownTrayIcon, CogIcon } from '@heroicons/vue/24/outline'
import type { Task } from '@/stores/tasks'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'

interface Props {
  isOpen: boolean
  task: Task | null
}

interface Emits {
  (e: 'close'): void
}

defineProps<Props>()
defineEmits<Emits>()

const formatDateTime = (dateString: string) => {
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(dateString))
}

const getTaskTypeText = (taskType: string) => {
  const typeMap: Record<string, string> = {
    parse_serp: 'Парсинг SERP',
    check_positions: 'Проверка позиций',
    warmup_profile: 'Прогрев профиля'
  }
  return typeMap[taskType] || taskType
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

const downloadResults = () => {
  // Логика скачивания результатов в CSV формате
  console.log('Download results')
}
</script>
