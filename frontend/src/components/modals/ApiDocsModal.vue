<template>
  <Modal
    :isOpen="isOpen"
    title="API Документация"
    panel-class="max-w-4xl"
    @close="$emit('close')"
  >
    <div class="max-h-96 overflow-y-auto">
      <div class="space-y-6">
        <!-- Authentication -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">Аутентификация</h3>
          <p class="text-sm text-gray-600 mb-3">
            Для доступа к API используйте ваш API ключ в query параметре или заголовке:
          </p>
          <div class="bg-gray-50 rounded-md p-4 font-mono text-sm">
            <div class="mb-2">
              <span class="text-green-600"># Query parameter</span><br>
              GET /api/v1/domains/api/list?api_key=YOUR_API_KEY
            </div>
            <div>
              <span class="text-green-600"># Header</span><br>
              X-API-Key: YOUR_API_KEY
            </div>
          </div>
        </div>

        <!-- Domains API -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">Управление доменами</h3>

          <!-- Get domains -->
          <div class="mb-4">
            <h4 class="text-md font-medium text-gray-800 mb-2">Получить список доменов</h4>
            <div class="bg-gray-50 rounded-md p-4 font-mono text-sm">
              <span class="text-blue-600">GET</span> /api/v1/domains/api/list
            </div>
            <p class="text-sm text-gray-600 mt-2">
              Возвращает список всех доменов пользователя с количеством ключевых слов.
            </p>
          </div>

          <!-- Add domain -->
          <div class="mb-4">
            <h4 class="text-md font-medium text-gray-800 mb-2">Добавить домен</h4>
            <div class="bg-gray-50 rounded-md p-4 font-mono text-sm">
              <span class="text-green-600">POST</span> /api/v1/domains/api/add<br>
              Content-Type: application/json<br><br>
              {<br>
              &nbsp;&nbsp;"domain": "example.com"<br>
              }
            </div>
          </div>
        </div>

        <!-- Tasks API -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">Управление задачами</h3>

          <!-- Create parse task -->
          <div class="mb-4">
            <h4 class="text-md font-medium text-gray-800 mb-2">Создать задачу парсинга</h4>
            <div class="bg-gray-50 rounded-md p-4 font-mono text-sm">
              <span class="text-green-600">POST</span> /api/v1/tasks/api/parse<br>
              Content-Type: application/json<br><br>
              {<br>
              &nbsp;&nbsp;"keyword": "купить телефон",<br>
              &nbsp;&nbsp;"device_type": "desktop", <span class="text-gray-500">// или "mobile"</span><br>
              &nbsp;&nbsp;"pages": 10,<br>
              &nbsp;&nbsp;"region_code": "213" <span class="text-gray-500">// код региона</span><br>
              }
            </div>
          </div>

          <!-- Get task status -->
          <div class="mb-4">
            <h4 class="text-md font-medium text-gray-800 mb-2">Получить статус задачи</h4>
            <div class="bg-gray-50 rounded-md p-4 font-mono text-sm">
              <span class="text-blue-600">GET</span> /api/v1/tasks/api/status/{task_id}
            </div>
            <p class="text-sm text-gray-600 mt-2">
              Возвращает текущий статус задачи и результаты (если завершена).
            </p>
          </div>
        </div>

        <!-- Billing API -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">Биллинг</h3>

          <!-- Get balance -->
          <div class="mb-4">
            <h4 class="text-md font-medium text-gray-800 mb-2">Получить баланс</h4>
            <div class="bg-gray-50 rounded-md p-4 font-mono text-sm">
              <span class="text-blue-600">GET</span> /api/v1/billing/api/balance
            </div>
            <p class="text-sm text-gray-600 mt-2">
              Возвращает текущий, доступный и зарезервированный баланс.
            </p>
          </div>
        </div>

        <!-- Response examples -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">Примеры ответов</h3>

          <div class="mb-4">
            <h4 class="text-md font-medium text-gray-800 mb-2">Успешный ответ создания задачи</h4>
            <div class="bg-gray-50 rounded-md p-4 font-mono text-sm">
              {<br>
              &nbsp;&nbsp;"success": true,<br>
              &nbsp;&nbsp;"task_id": "550e8400-e29b-41d4-a716-446655440000",<br>
              &nbsp;&nbsp;"estimated_cost": 1.00<br>
              }
            </div>
          </div>

          <div class="mb-4">
            <h4 class="text-md font-medium text-gray-800 mb-2">Статус завершенной задачи</h4>
            <div class="bg-gray-50 rounded-md p-4 font-mono text-sm">
              {<br>
              &nbsp;&nbsp;"task_id": "550e8400-e29b-41d4-a716-446655440000",<br>
              &nbsp;&nbsp;"status": "completed",<br>
              &nbsp;&nbsp;"task_type": "parse_serp",<br>
              &nbsp;&nbsp;"created_at": "2024-01-15T10:30:00",<br>
              &nbsp;&nbsp;"completed_at": "2024-01-15T10:32:15",<br>
              &nbsp;&nbsp;"result": {<br>
              &nbsp;&nbsp;&nbsp;&nbsp;"keyword": "купить телефон",<br>
              &nbsp;&nbsp;&nbsp;&nbsp;"results_count": 95,<br>
              &nbsp;&nbsp;&nbsp;&nbsp;"device_type": "desktop"<br>
              &nbsp;&nbsp;}<br>
              }
            </div>
          </div>
        </div>

        <!-- Error codes -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 mb-3">Коды ошибок</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="font-mono">400</span>
              <span class="text-gray-600">Некорректные параметры запроса</span>
            </div>
            <div class="flex justify-between">
              <span class="font-mono">401</span>
              <span class="text-gray-600">Неверный или отсутствующий API ключ</span>
            </div>
            <div class="flex justify-between">
              <span class="font-mono">402</span>
              <span class="text-gray-600">Недостаточно средств на балансе</span>
            </div>
            <div class="flex justify-between">
              <span class="font-mono">429</span>
              <span class="text-gray-600">Превышен лимит запросов</span>
            </div>
            <div class="flex justify-between">
              <span class="font-mono">500</span>
              <span class="text-gray-600">Внутренняя ошибка сервера</span>
            </div>
          </div>
        </div>
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
import Modal from '@/components/ui/Modal.vue'

interface Props {
  isOpen: boolean
}

interface Emits {
  (e: 'close'): void
}

defineProps<Props>()
defineEmits<Emits>()
</script>
