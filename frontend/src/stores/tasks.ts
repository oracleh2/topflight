import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'

export interface Task {
  task_id: string
  task_type: string
  status: string
  created_at: string
  started_at?: string
  completed_at?: string
  parameters: any
  result?: any
  error_message?: string
}

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function createParseTask(keyword: string, deviceType: string, pages = 10, regionCode = '213') {
    try {
      loading.value = true
      error.value = null

      const response = await api.createParseTask(keyword, deviceType, pages, regionCode)
      await fetchUserTasks() // Обновляем список задач
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка создания задачи'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createPositionCheckTask(keywordIds: string[], deviceType: string) {
    try {
      loading.value = true
      error.value = null

      const response = await api.createPositionCheckTask(keywordIds, deviceType)
      await fetchUserTasks() // Обновляем список задач
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка создания задачи проверки позиций'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchUserTasks(limit = 50, offset = 0, status?: string) {
    try {
      loading.value = true
      const response = await api.getUserTasks(limit, offset, status)

      if (offset === 0) {
        tasks.value = response.data
      } else {
        tasks.value.push(...response.data)
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки задач'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getTaskStatus(taskId: string) {
    try {
      const response = await api.getTaskStatus(taskId)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка получения статуса задачи'
      throw err
    }
  }

  return {
    tasks,
    loading,
    error,
    createParseTask,
    createPositionCheckTask,
    fetchUserTasks,
    getTaskStatus
  }
})
