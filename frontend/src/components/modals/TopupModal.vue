<template>
  <Modal
    :isOpen="isOpen"
    title="Пополнить баланс"
    panel-class="max-w-md"
    @close="$emit('close')"
  >
    <form @submit.prevent="handleSubmit">
      <div class="space-y-4">
        <div>
          <label for="amount" class="block text-sm font-medium text-gray-700">
            Сумма пополнения
          </label>
          <div class="mt-1 relative rounded-md shadow-sm">
            <input
              id="amount"
              v-model.number="form.amount"
              type="number"
              min="1"
              max="100000"
              step="0.01"
              class="input pr-12"
              :class="{ 'border-red-500': errors.amount }"
              placeholder="1000.00"
              @input="clearError('amount')"
            />
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span class="text-gray-500 sm:text-sm">₽</span>
            </div>
          </div>
          <p v-if="errors.amount" class="mt-1 text-sm text-red-600">
            {{ errors.amount }}
          </p>
        </div>

        <!-- Quick amount buttons -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Быстрый выбор суммы
          </label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="amount in quickAmounts"
              :key="amount"
              type="button"
              @click="form.amount = amount"
              class="btn-secondary text-sm py-2"
            >
              {{ formatCurrency(amount) }}
            </button>
          </div>
        </div>

        <!-- Info about tariff upgrade -->
        <div v-if="form.amount >= 20000" class="rounded-md bg-blue-50 p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <InformationCircleIcon class="h-5 w-5 text-blue-400" aria-hidden="true" />
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-blue-800">
                Upgrade тарифа
              </h3>
              <div class="mt-2 text-sm text-blue-700">
                <p>
                  При пополнении от 20,000 ₽ в месяц ваш тариф автоматически изменится на "Премиум"
                  со скидкой 20% на все проверки.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Current balance info -->
        <div class="rounded-md bg-gray-50 p-4">
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-500">Текущий баланс:</span>
            <span class="text-sm font-medium text-gray-900">
              {{ formatCurrency(billingStore.balance?.current_balance || 0) }}
            </span>
          </div>
          <div v-if="form.amount > 0" class="flex justify-between items-center mt-2 pt-2 border-t border-gray-200">
            <span class="text-sm text-gray-500">После пополнения:</span>
            <span class="text-sm font-semibold text-green-600">
              {{ formatCurrency((billingStore.balance?.current_balance || 0) + form.amount) }}
            </span>
          </div>
        </div>
      </div>

      <Alert
        v-if="billingStore.error"
        type="error"
        :message="billingStore.error"
        class="mt-4"
        dismissible
        @dismiss="billingStore.error = null"
      />

      <!-- Test mode warning -->
      <Alert
        type="warning"
        title="Тестовый режим"
        message="Это тестовое пополнение баланса. В продакшн версии здесь будет интеграция с платежной системой."
        class="mt-4"
      />
    </form>

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
        :disabled="billingStore.loading || form.amount <= 0"
      >
        <Spinner v-if="billingStore.loading" class="mr-2 h-4 w-4" />
        Пополнить {{ formatCurrency(form.amount || 0) }}
      </button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { InformationCircleIcon } from '@heroicons/vue/24/outline'
import { useBillingStore } from '@/stores/billing'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
  isOpen: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'success'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const billingStore = useBillingStore()

const form = reactive({
  amount: 0
})

const errors = ref<Record<string, string>>({})

const quickAmounts = [500, 1000, 2000, 5000, 10000, 20000]

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

const validateForm = () => {
  errors.value = {}

  if (!form.amount || form.amount <= 0) {
    errors.value.amount = 'Сумма должна быть больше нуля'
  } else if (form.amount > 100000) {
    errors.value.amount = 'Максимальная сумма пополнения: 100,000 ₽'
  } else if (form.amount < 1) {
    errors.value.amount = 'Минимальная сумма пополнения: 1 ₽'
  }

  return Object.keys(errors.value).length === 0
}

const clearError = (field: string) => {
  if (errors.value[field]) {
    delete errors.value[field]
  }
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    await billingStore.topupBalance(form.amount)

    // Сбрасываем форму
    form.amount = 0
    errors.value = {}

    emit('success')
  } catch (error) {
    console.error('Error topping up balance:', error)
  }
}
</script>
