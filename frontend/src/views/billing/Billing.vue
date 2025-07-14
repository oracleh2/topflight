<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="sm:flex sm:items-center">
      <div class="sm:flex-auto">
        <h1 class="text-xl font-semibold text-gray-900">Биллинг</h1>
        <p class="mt-2 text-sm text-gray-700">
          Управление балансом, тарифами и платежами
        </p>
      </div>
    </div>

    <!-- Balance and tariff cards -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Balance card -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900 flex items-center">
            <CurrencyDollarIcon class="mr-2 h-5 w-5 text-gray-400" />
            Баланс
          </h3>
        </div>
        <div class="px-6 py-4 space-y-4">
          <div class="flex justify-between items-center">
            <span class="text-sm text-gray-500">Доступный баланс</span>
            <span class="text-2xl font-bold text-gray-900">
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
            <span class="text-sm text-gray-500">Общий баланс</span>
            <span class="text-sm font-medium text-gray-900">
              {{ formatCurrency(billingStore.balance?.current_balance || 0) }}
            </span>
          </div>

          <div class="pt-4 border-t border-gray-200">
            <button
              @click="showTopupModal = true"
              class="btn-primary w-full"
            >
              Пополнить баланс
            </button>
          </div>
        </div>
      </div>

      <!-- Tariff card -->
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900 flex items-center">
            <StarIcon class="mr-2 h-5 w-5 text-gray-400" />
            Текущий тариф
          </h3>
        </div>
        <div class="px-6 py-4 space-y-4">
          <div v-if="billingStore.currentTariff" class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">Название</span>
              <span class="text-lg font-semibold text-gray-900">
                {{ billingStore.currentTariff.name }}
              </span>
            </div>

            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">Стоимость проверки</span>
              <span class="text-sm font-medium text-gray-900">
                {{ formatCurrency(billingStore.currentTariff.cost_per_check) }}
              </span>
            </div>

            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">Привязка к серверам</span>
              <span
                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  billingStore.currentTariff.server_binding_allowed
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                ]"
              >
                {{ billingStore.currentTariff.server_binding_allowed ? 'Доступна' : 'Недоступна' }}
              </span>
            </div>

            <div v-if="billingStore.currentTariff.min_monthly_topup > 0" class="text-xs text-gray-500">
              Для получения этого тарифа необходимо пополнение от
              {{ formatCurrency(billingStore.currentTariff.min_monthly_topup) }} в месяц
            </div>
          </div>

          <div v-else class="text-center py-4">
            <Spinner class="h-6 w-6 text-primary-600 mx-auto" />
          </div>
        </div>
      </div>
    </div>

    <!-- Cost calculator -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900 flex items-center">
          <CalculatorIcon class="mr-2 h-5 w-5 text-gray-400" />
          Калькулятор стоимости
        </h3>
      </div>
      <div class="px-6 py-4">
        <div class="max-w-md">
          <label for="checksCount" class="block text-sm font-medium text-gray-700">
            Количество проверок
          </label>
          <div class="mt-1 flex rounded-md shadow-sm">
            <input
              id="checksCount"
              v-model.number="checksCount"
              type="number"
              min="1"
              max="10000"
              class="input rounded-r-none"
              placeholder="100"
            />
            <button
              @click="calculateCost"
              class="btn-primary rounded-l-none border-l-0"
              :disabled="billingStore.loading"
            >
              <Spinner v-if="billingStore.loading" class="mr-2 h-4 w-4" />
              Рассчитать
            </button>
          </div>

          <div v-if="calculatedCost" class="mt-4 p-4 bg-gray-50 rounded-md">
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">Общая стоимость:</span>
              <span class="text-lg font-semibold text-gray-900">
                {{ formatCurrency(calculatedCost.total_cost) }}
              </span>
            </div>
            <div class="flex justify-between items-center mt-1">
              <span class="text-xs text-gray-500">За проверку:</span>
              <span class="text-xs text-gray-600">
                {{ formatCurrency(calculatedCost.cost_per_check) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transaction history -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-medium text-gray-900 flex items-center">
          <ClockIcon class="mr-2 h-5 w-5 text-gray-400" />
          История транзакций
        </h3>
      </div>

      <div v-if="billingStore.loading && !billingStore.transactions.length" class="flex justify-center py-12">
        <Spinner class="h-8 w-8 text-primary-600" />
      </div>

      <div v-else-if="!billingStore.transactions.length" class="px-6 py-12 text-center">
        <p class="text-gray-500">Транзакций пока нет</p>
      </div>

      <div v-else class="divide-y divide-gray-200">
        <div
          v-for="transaction in billingStore.transactions"
          :key="transaction.id"
          class="px-6 py-4 hover:bg-gray-50"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center min-w-0 flex-1">
              <div
                :class="[
                  'flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center',
                  getTransactionIconBg(transaction.type)
                ]"
              >
                <component
                  :is="getTransactionIcon(transaction.type)"
                  :class="[
                    'h-5 w-5',
                    getTransactionIconColor(transaction.type)
                  ]"
                />
              </div>

              <div class="ml-4 min-w-0 flex-1">
                <p class="text-sm font-medium text-gray-900">
                  {{ transaction.description }}
                </p>
                <p class="text-sm text-gray-500">
                  {{ formatDateTime(transaction.created_at) }}
                </p>
              </div>
            </div>

            <div class="ml-4 flex items-center">
              <span
                :class="[
                  'text-sm font-medium',
                  transaction.amount > 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                {{ transaction.amount > 0 ? '+' : '' }}{{ formatCurrency(transaction.amount) }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="canLoadMore" class="px-6 py-4 text-center">
          <button
            @click="loadMoreTransactions"
            class="btn-secondary"
            :disabled="billingStore.loading"
          >
            <Spinner v-if="billingStore.loading" class="mr-2 h-4 w-4" />
            Загрузить еще
          </button>
        </div>
      </div>
    </div>

    <!-- Topup modal -->
    <TopupModal
      :isOpen="showTopupModal"
      @close="showTopupModal = false"
      @success="handleTopupSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  CurrencyDollarIcon,
  StarIcon,
  CalculatorIcon,
  ClockIcon,
  PlusIcon,
  MinusIcon,
} from '@heroicons/vue/24/outline'
import { useBillingStore } from '@/stores/billing'
import Spinner from '@/components/ui/Spinner.vue'
import TopupModal from '@/components/modals/TopupModal.vue'

const billingStore = useBillingStore()

const showTopupModal = ref(false)
const checksCount = ref(100)
const calculatedCost = ref<any>(null)
const currentPage = ref(0)
const pageSize = 20

const canLoadMore = computed(() => {
  return billingStore.transactions.length >= (currentPage.value + 1) * pageSize
})

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 2
  }).format(amount)
}

const formatDateTime = (dateString: string) => {
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(dateString))
}

const getTransactionIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    topup: PlusIcon,
    charge: MinusIcon,
    refund: PlusIcon
  }
  return iconMap[type] || PlusIcon
}

const getTransactionIconBg = (type: string) => {
  const bgMap: Record<string, string> = {
    topup: 'bg-green-100',
    charge: 'bg-red-100',
    refund: 'bg-blue-100'
  }
  return bgMap[type] || 'bg-gray-100'
}

const getTransactionIconColor = (type: string) => {
  const colorMap: Record<string, string> = {
    topup: 'text-green-600',
    charge: 'text-red-600',
    refund: 'text-blue-600'
  }
  return colorMap[type] || 'text-gray-600'
}

const calculateCost = async () => {
  if (checksCount.value < 1) return

  try {
    calculatedCost.value = await billingStore.calculateCheckCost(checksCount.value)
  } catch (error) {
    console.error('Error calculating cost:', error)
  }
}

const loadMoreTransactions = async () => {
  currentPage.value += 1
  try {
    await billingStore.fetchTransactionHistory(pageSize, currentPage.value * pageSize)
  } catch (error) {
    console.error('Error loading more transactions:', error)
    currentPage.value -= 1
  }
}

const handleTopupSuccess = () => {
  showTopupModal.value = false
  // Обновляем данные
  billingStore.fetchBalance()
  billingStore.fetchTransactionHistory(pageSize, 0)
  currentPage.value = 0
}

onMounted(async () => {
  try {
    await Promise.all([
      billingStore.fetchBalance(),
      billingStore.fetchCurrentTariff(),
      billingStore.fetchTransactionHistory(pageSize, 0)
    ])
  } catch (error) {
    console.error('Error loading billing data:', error)
  }
})
</script>
