<template>
  <Modal
    :isOpen="isOpen"
    title="Проверить позиции"
    panel-class="max-w-md"
    @close="$emit('close')"
  >
    <div class="space-y-4">
      <div>
        <p class="text-sm text-gray-600">
          Будет выполнена проверка позиций для <strong>{{ keywordIds.length }}</strong>
          {{ keywordIds.length === 1 ? 'ключевого слова' : 'ключевых слов' }}.
        </p>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700">
          Тип устройства
        </label>
        <div class="mt-2 space-y-2">
          <label class="flex items-center">
            <input
              v-model="deviceType"
              type="radio"
              value="desktop"
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
            />
            <span class="ml-2 text-sm text-gray-700 flex items-center">
              <ComputerDesktopIcon class="mr-1 h-4 w-4" />
              Десктоп
            </span>
          </label>
          <label class="flex items-center">
            <input
              v-model="deviceType"
              type="radio"
              value="mobile"
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
            />
            <span class="ml-2 text-sm text-gray-700 flex items-center">
              <DevicePhoneMobileIcon class="mr-1 h-4 w-4" />
              Мобильный
            </span>
          </label>
        </div>
      </div>

      <!-- Cost estimation -->
      <div v-if="estimatedCost" class="rounded-md bg-blue-50 p-4">
        <div class="flex justify-between items-center">
          <span class="text-sm text-blue-700">Ориентировочная стоимость:</span>
          <span class="text-sm font-semibold text-blue-900">
            {{ formatCurrency(estimatedCost) }}
          </span>
        </div>
      </div>

      <Alert
        v-if="tasksStore.error"
        type="error"
        :message="tasksStore.error"
        dismissible
        @dismiss="tasksStore.error = null"
      />
    </div>

    <template #actions>
      <button
        type="button"
        class="btn-secondary"
        @click="$emit('close')"
      >
        Отмена
      </button>
      <button
        type="button"
        class="btn-primary ml-3"
        @click="handleSubmit"
        :disabled="tasksStore.loading"
      >
        <Spinner v-if="tasksStore.loading" class="mr-2 h-4 w-4" />
        Проверить позиции
      </button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ComputerDesktopIcon, DevicePhoneMobileIcon } from '@heroicons/vue/24/outline'
import { useTasksStore } from '@/stores/tasks'
import { useBillingStore } from '@/stores/billing'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
  isOpen: boolean
  keywordIds: string[]
}

interface Emits {
  (e: 'close'): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const tasksStore = useTasksStore()
const billingStore = useBillingStore()

const deviceType = ref('desktop')
const estimatedCost = ref(0)

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 2
  }).format(amount)
}

const calculateCost = async () => {
  if (props.keywordIds.length === 0) return

  try {
    const result = await billingStore.calculateCheckCost(props.keywordIds.length)
    estimatedCost.value = result.total_cost
  } catch (error) {
    console.error('Error calculating cost:', error)
  }
}

const handleSubmit = async () => {
  try {
    await tasksStore.createPositionCheckTask(props.keywordIds, deviceType.value)
    emit('success')
  } catch (error) {
    console.error('Error creating position check task:', error)
  }
}

// Рассчитываем стоимость при изменении количества ключевых слов
watch(() => props.keywordIds, calculateCost, { immediate: true })
</script>
