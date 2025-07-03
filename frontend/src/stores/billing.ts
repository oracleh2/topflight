import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'

export interface Balance {
  current_balance: number
  reserved_balance: number
  available_balance: number
}

export interface Transaction {
  id: string
  amount: number
  type: string
  description: string
  created_at: string
}

export interface Tariff {
  id: string
  name: string
  description: string
  cost_per_check: number
  min_monthly_topup: number
  server_binding_allowed: boolean
  priority_level: number
}

export const useBillingStore = defineStore('billing', () => {
  const balance = ref<Balance | null>(null)
  const transactions = ref<Transaction[]>([])
  const currentTariff = ref<Tariff | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchBalance() {
    try {
      loading.value = true
      const response = await api.getBalance()
      balance.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки баланса'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function topupBalance(amount: number) {
    try {
      loading.value = true
      error.value = null

      const response = await api.topupBalance(amount)
      await fetchBalance() // Обновляем баланс
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка пополнения баланса'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentTariff() {
    try {
      const response = await api.getCurrentTariff()
      currentTariff.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки тарифа'
      throw err
    }
  }

  async function fetchTransactionHistory(limit = 50, offset = 0) {
    try {
      loading.value = true
      const response = await api.getTransactionHistory(limit, offset)

      if (offset === 0) {
        transactions.value = response.data
      } else {
        transactions.value.push(...response.data)
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки истории транзакций'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function calculateCheckCost(checksCount = 1) {
    try {
      const response = await api.calculateCheckCost(checksCount)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка расчета стоимости'
      throw err
    }
  }

  return {
    balance,
    transactions,
    currentTariff,
    loading,
    error,
    fetchBalance,
    topupBalance,
    fetchCurrentTariff,
    fetchTransactionHistory,
    calculateCheckCost
  }
})
