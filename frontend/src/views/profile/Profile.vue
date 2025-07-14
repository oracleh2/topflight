<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-xl font-semibold text-gray-900">Профиль</h1>
      <p class="mt-2 text-sm text-gray-700">
        Управление настройками аккаунта и API доступом
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main profile info -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Account information -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-medium text-gray-900">Информация об аккаунте</h3>
          </div>
          <div class="px-6 py-4 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Email</label>
              <div class="mt-1 flex items-center">
                <input
                  type="email"
                  :value="authStore.user?.email"
                  readonly
                  class="input bg-gray-50 cursor-not-allowed"
                />
              </div>
              <p class="mt-1 text-xs text-gray-500">
                Email нельзя изменить. Обратитесь в поддержку если нужно изменить email.
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Дата регистрации</label>
              <div class="mt-1">
                <input
                  type="text"
                  :value="formatDate(authStore.user?.created_at)"
                  readonly
                  class="input bg-gray-50 cursor-not-allowed"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Текущий тариф</label>
              <div class="mt-1 flex items-center justify-between">
                <input
                  type="text"
                  :value="authStore.user?.subscription_plan || 'Базовый'"
                  readonly
                  class="input bg-gray-50 cursor-not-allowed flex-1"
                />
                <router-link
                  to="/billing"
                  class="ml-3 btn-secondary text-sm"
                >
                  Изменить
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Change password -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-medium text-gray-900">Изменить пароль</h3>
          </div>
          <div class="px-6 py-4">
            <form @submit.prevent="handlePasswordChange" class="space-y-4">
              <div>
                <label for="currentPassword" class="block text-sm font-medium text-gray-700">
                  Текущий пароль
                </label>
                <input
                  id="currentPassword"
                  v-model="passwordForm.currentPassword"
                  type="password"
                  class="input mt-1"
                  :class="{ 'border-red-500': passwordErrors.currentPassword }"
                  @input="clearPasswordError('currentPassword')"
                />
                <p v-if="passwordErrors.currentPassword" class="mt-1 text-sm text-red-600">
                  {{ passwordErrors.currentPassword }}
                </p>
              </div>

              <div>
                <label for="newPassword" class="block text-sm font-medium text-gray-700">
                  Новый пароль
                </label>
                <input
                  id="newPassword"
                  v-model="passwordForm.newPassword"
                  type="password"
                  class="input mt-1"
                  :class="{ 'border-red-500': passwordErrors.newPassword }"
                  @input="clearPasswordError('newPassword')"
                />
                <p v-if="passwordErrors.newPassword" class="mt-1 text-sm text-red-600">
                  {{ passwordErrors.newPassword }}
                </p>
                <p class="mt-1 text-xs text-gray-500">
                  Минимум 8 символов, включая заглавные и строчные буквы, цифры
                </p>
              </div>

              <div>
                <label for="confirmPassword" class="block text-sm font-medium text-gray-700">
                  Подтвердите новый пароль
                </label>
                <input
                  id="confirmPassword"
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  class="input mt-1"
                  :class="{ 'border-red-500': passwordErrors.confirmPassword }"
                  @input="clearPasswordError('confirmPassword')"
                />
                <p v-if="passwordErrors.confirmPassword" class="mt-1 text-sm text-red-600">
                  {{ passwordErrors.confirmPassword }}
                </p>
              </div>

              <Alert
                v-if="authStore.error"
                type="error"
                :message="authStore.error"
                dismissible
                @dismiss="authStore.error = null"
              />

              <Alert
                v-if="passwordChangeSuccess"
                type="success"
                message="Пароль успешно изменен"
                dismissible
                @dismiss="passwordChangeSuccess = false"
              />

              <div class="flex justify-end">
                <button
                  type="submit"
                  class="btn-primary"
                  :disabled="authStore.loading"
                >
                  <Spinner v-if="authStore.loading" class="mr-2 h-4 w-4" />
                  Изменить пароль
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- API Access -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-medium text-gray-900 flex items-center">
              <KeyIcon class="mr-2 h-5 w-5 text-gray-400" />
              API доступ
            </h3>
          </div>
          <div class="px-6 py-4 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">API ключ</label>
              <div class="mt-1 flex">
                <input
                  :type="showApiKey ? 'text' : 'password'"
                  :value="authStore.user?.api_key"
                  readonly
                  class="input rounded-r-none bg-gray-50 cursor-not-allowed flex-1 font-mono text-sm"
                />
                <button
                  type="button"
                  @click="showApiKey = !showApiKey"
                  class="btn-secondary rounded-l-none border-l-0 px-3"
                >
                  <EyeIcon v-if="!showApiKey" class="h-4 w-4" />
                  <EyeSlashIcon v-else class="h-4 w-4" />
                </button>
              </div>
              <p class="mt-1 text-xs text-gray-500">
                Используйте этот ключ для доступа к API
              </p>
            </div>

            <div class="flex space-x-3">
              <button
                @click="copyApiKey"
                class="btn-secondary text-sm flex-1"
              >
                <ClipboardDocumentIcon class="mr-1 h-4 w-4" />
                {{ copiedApiKey ? 'Скопировано!' : 'Копировать' }}
              </button>
              <button
                @click="regenerateApiKey"
                class="btn-secondary text-sm flex-1"
                :disabled="authStore.loading"
              >
                <Spinner v-if="authStore.loading" class="mr-1 h-4 w-4" />
                <ArrowPathIcon v-else class="mr-1 h-4 w-4" />
                Обновить
              </button>
            </div>

            <Alert
              v-if="apiKeyRegenerated"
              type="success"
              message="API ключ успешно обновлен"
              dismissible
              @dismiss="apiKeyRegenerated = false"
            />
          </div>
        </div>

        <!-- Account stats -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-medium text-gray-900">Статистика</h3>
          </div>
          <div class="px-6 py-4 space-y-3">
            <div class="flex justify-between">
              <span class="text-sm text-gray-500">Доменов</span>
              <span class="text-sm font-medium text-gray-900">
                {{ authStore.user?.domains_count || 0 }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-gray-500">Ключевых слов</span>
              <span class="text-sm font-medium text-gray-900">
                {{ authStore.user?.keywords_count || 0 }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-gray-500">Баланс</span>
              <span class="text-sm font-medium text-gray-900">
                {{ formatCurrency(authStore.user?.balance || 0) }}
              </span>
            </div>
            <div v-if="authStore.user?.last_topup_date" class="flex justify-between">
              <span class="text-sm text-gray-500">Последнее пополнение</span>
              <span class="text-sm text-gray-600">
                {{ formatDate(authStore.user.last_topup_date) }}
              </span>
            </div>
          </div>
        </div>

        <!-- API Documentation link -->
        <div class="bg-white shadow rounded-lg">
          <div class="px-6 py-4">
            <h3 class="text-lg font-medium text-gray-900 mb-4">Документация</h3>
            <div class="space-y-3">
              <a
                href="#"
                @click.prevent="showApiDocsModal = true"
                class="flex items-center p-3 rounded-md border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <DocumentTextIcon class="h-5 w-5 text-gray-400 mr-3" />
                <div>
                  <p class="text-sm font-medium text-gray-900">API документация</p>
                  <p class="text-xs text-gray-500">Примеры использования API</p>
                </div>
              </a>

              <a
                href="#"
                @click.prevent="downloadPostmanCollection"
                class="flex items-center p-3 rounded-md border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <ArrowDownTrayIcon class="h-5 w-5 text-gray-400 mr-3" />
                <div>
                  <p class="text-sm font-medium text-gray-900">Postman коллекция</p>
                  <p class="text-xs text-gray-500">Готовые запросы для тестирования</p>
                </div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- API Documentation Modal -->
    <ApiDocsModal
      :isOpen="showApiDocsModal"
      @close="showApiDocsModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import {
  KeyIcon,
  EyeIcon,
  EyeSlashIcon,
  ClipboardDocumentIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import Spinner from '@/components/ui/Spinner.vue'
import Alert from '@/components/ui/Alert.vue'
import ApiDocsModal from '@/components/modals/ApiDocsModal.vue'

const authStore = useAuthStore()

const showApiKey = ref(false)
const copiedApiKey = ref(false)
const apiKeyRegenerated = ref(false)
const passwordChangeSuccess = ref(false)
const showApiDocsModal = ref(false)

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordErrors = ref<Record<string, string>>({})

const formatDate = (dateString?: string) => {
  if (!dateString) return 'Неизвестно'
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).format(new Date(dateString))
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 2
  }).format(amount)
}

const validatePasswordForm = () => {
  passwordErrors.value = {}

  if (!passwordForm.currentPassword) {
    passwordErrors.value.currentPassword = 'Введите текущий пароль'
  }

  if (!passwordForm.newPassword) {
    passwordErrors.value.newPassword = 'Введите новый пароль'
  } else if (passwordForm.newPassword.length < 8) {
    passwordErrors.value.newPassword = 'Пароль должен содержать минимум 8 символов'
  } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(passwordForm.newPassword)) {
    passwordErrors.value.newPassword = 'Пароль должен содержать заглавные и строчные буквы, цифры'
  }

  if (!passwordForm.confirmPassword) {
    passwordErrors.value.confirmPassword = 'Подтвердите новый пароль'
  } else if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordErrors.value.confirmPassword = 'Пароли не совпадают'
  }

  return Object.keys(passwordErrors.value).length === 0
}

const clearPasswordError = (field: string) => {
  if (passwordErrors.value[field]) {
    delete passwordErrors.value[field]
  }
}

const handlePasswordChange = async () => {
  if (!validatePasswordForm()) {
    return
  }

  const success = await authStore.changePassword(
    passwordForm.currentPassword,
    passwordForm.newPassword
  )

  if (success) {
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    passwordErrors.value = {}
    passwordChangeSuccess.value = true
  }
}

const copyApiKey = async () => {
  if (!authStore.user?.api_key) return

  try {
    await navigator.clipboard.writeText(authStore.user.api_key)
    copiedApiKey.value = true
    setTimeout(() => {
      copiedApiKey.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy API key:', error)
  }
}

const regenerateApiKey = async () => {
  try {
    await authStore.regenerateApiKey()
    apiKeyRegenerated.value = true
    setTimeout(() => {
      apiKeyRegenerated.value = false
    }, 3000)
  } catch (error) {
    console.error('Failed to regenerate API key:', error)
  }
}

const downloadPostmanCollection = () => {
  const collection = {
    info: {
      name: "Yandex Parser API",
      description: "API для мониторинга позиций в Яндексе",
      version: "1.0.0"
    },
    auth: {
      type: "bearer",
      bearer: [
        {
          key: "token",
          value: "{{api_key}}",
          type: "string"
        }
      ]
    },
    variable: [
      {
        key: "base_url",
        value: "http://localhost:8000/api/v1"
      },
      {
        key: "api_key",
        value: authStore.user?.api_key || "YOUR_API_KEY"
      }
    ],
    item: [
      {
        name: "Domains",
        item: [
          {
            name: "Get Domains",
            request: {
              method: "GET",
              header: [],
              url: {
                raw: "{{base_url}}/domains/api/list?api_key={{api_key}}",
                host: ["{{base_url}}"],
                path: ["domains", "api", "list"],
                query: [
                  {
                    key: "api_key",
                    value: "{{api_key}}"
                  }
                ]
              }
            }
          },
          {
            name: "Add Domain",
            request: {
              method: "POST",
              header: [
                {
                  key: "Content-Type",
                  value: "application/json"
                }
              ],
              body: {
                mode: "raw",
                raw: JSON.stringify({
                  domain: "example.com"
                })
              },
              url: {
                raw: "{{base_url}}/domains/api/add?api_key={{api_key}}",
                host: ["{{base_url}}"],
                path: ["domains", "api", "add"],
                query: [
                  {
                    key: "api_key",
                    value: "{{api_key}}"
                  }
                ]
              }
            }
          }
        ]
      },
      {
        name: "Tasks",
        item: [
          {
            name: "Create Parse Task",
            request: {
              method: "POST",
              header: [
                {
                  key: "Content-Type",
                  value: "application/json"
                }
              ],
              body: {
                mode: "raw",
                raw: JSON.stringify({
                  keyword: "test query",
                  device_type: "desktop",
                  pages: 10,
                  region_code: "213"
                })
              },
              url: {
                raw: "{{base_url}}/tasks/api/parse?api_key={{api_key}}",
                host: ["{{base_url}}"],
                path: ["tasks", "api", "parse"],
                query: [
                  {
                    key: "api_key",
                    value: "{{api_key}}"
                  }
                ]
              }
            }
          },
          {
            name: "Get Task Status",
            request: {
              method: "GET",
              header: [],
              url: {
                raw: "{{base_url}}/tasks/api/status/{{task_id}}?api_key={{api_key}}",
                host: ["{{base_url}}"],
                path: ["tasks", "api", "status", "{{task_id}}"],
                query: [
                  {
                    key: "api_key",
                    value: "{{api_key}}"
                  }
                ]
              }
            }
          }
        ]
      },
      {
        name: "Billing",
        item: [
          {
            name: "Get Balance",
            request: {
              method: "GET",
              header: [],
              url: {
                raw: "{{base_url}}/billing/api/balance?api_key={{api_key}}",
                host: ["{{base_url}}"],
                path: ["billing", "api", "balance"],
                query: [
                  {
                    key: "api_key",
                    value: "{{api_key}}"
                  }
                ]
              }
            }
          }
        ]
      }
    ]
  }

  const blob = new Blob([JSON.stringify(collection, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'yandex-parser-api.postman_collection.json'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>
