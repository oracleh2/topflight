<!-- frontend/src/components/proxy/ProxyImportModal.vue -->
<template>
  <TransitionRoot as="template" :show="isOpen">
    <Dialog as="div" class="relative z-50" @close="$emit('close')">
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild
            as="template"
            enter="ease-out duration-300"
            enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enter-to="opacity-100 translate-y-0 sm:scale-100"
            leave="ease-in duration-200"
            leave-from="opacity-100 translate-y-0 sm:scale-100"
            leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          >
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl sm:p-6">
              <!-- Заголовок -->
              <div class="flex items-center justify-between mb-6">
                <DialogTitle as="h3" class="text-lg font-medium text-gray-900">
                  Импорт прокси
                </DialogTitle>
                <button
                  @click="$emit('close')"
                  class="rounded-md bg-white text-gray-400 hover:text-gray-500"
                >
                  <XMarkIcon class="h-6 w-6" />
                </button>
              </div>

              <!-- Выбор типа прокси -->
              <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Тип прокси
                </label>
                <div class="grid grid-cols-2 gap-3">
                  <button
                    @click="selectedProxyType = 'warmup'"
                    :class="[
                      selectedProxyType === 'warmup'
                        ? 'bg-primary-100 border-primary-300 text-primary-900'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50',
                      'border rounded-md px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-500'
                    ]"
                  >
                    <UserIcon class="h-4 w-4 inline mr-2" />
                    Для нагула профилей
                  </button>
                  <button
                    @click="selectedProxyType = 'parsing'"
                    :class="[
                      selectedProxyType === 'parsing'
                        ? 'bg-primary-100 border-primary-300 text-primary-900'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50',
                      'border rounded-md px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-500'
                    ]"
                  >
                    <MagnifyingGlassIcon class="h-4 w-4 inline mr-2" />
                    Для замера позиций
                  </button>
                </div>
              </div>

              <!-- Табы методов импорта -->
              <div class="border-b border-gray-200 mb-6">
                <nav class="-mb-px flex space-x-8">
                  <button
                    v-for="tab in importTabs"
                    :key="tab.key"
                    @click="activeImportTab = tab.key"
                    :class="[
                      activeImportTab === tab.key
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                      'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center'
                    ]"
                  >
                    <component :is="tab.icon" class="h-4 w-4 mr-2" />
                    {{ tab.name }}
                  </button>
                </nav>
              </div>

              <!-- Контент табов -->
              <div class="space-y-6">
                <!-- Ручной ввод -->
                <div v-if="activeImportTab === 'manual'">
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Список прокси (по одной на строку)
                  </label>
                  <textarea
                    v-model="manualProxies"
                    rows="8"
                    class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Примеры:
192.168.1.100:8080:username:password
http://user:pass@proxy.example.com:3128
socks5://127.0.0.1:1080
192.168.1.200:8080"
                  ></textarea>
                  <div class="mt-2 flex justify-between">
                    <button
                      @click="showFormatsHelp = true"
                      class="text-sm text-primary-600 hover:text-primary-700"
                    >
                      Показать поддерживаемые форматы
                    </button>
                    <span class="text-sm text-gray-500">
                      {{ manualProxies.split('\n').filter(line => line.trim()).length }} прокси
                    </span>
                  </div>
                </div>

                <!-- Файл -->
                <div v-if="activeImportTab === 'file'">
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Загрузить файл с прокси (.txt, .csv)
                  </label>
                  <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      ref="fileInput"
                      type="file"
                      accept=".txt,.csv"
                      @change="handleFileSelect"
                      class="hidden"
                    >
                    <DocumentTextIcon class="mx-auto h-12 w-12 text-gray-300" />
                    <div class="mt-4">
                      <button
                        @click="$refs.fileInput.click()"
                        class="btn-primary"
                      >
                        Выбрать файл
                      </button>
                      <p class="mt-2 text-sm text-gray-500">
                        или перетащите файл сюда
                      </p>
                    </div>
                    <p v-if="selectedFile" class="mt-2 text-sm text-gray-900">
                      Выбран файл: {{ selectedFile.name }}
                    </p>
                  </div>
                </div>

                <!-- URL -->
                <div v-if="activeImportTab === 'url'">
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    URL со списком прокси
                  </label>
                  <input
                    v-model="proxyUrl"
                    type="url"
                    class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    placeholder="https://example.com/proxies.txt"
                  >
                  <p class="mt-2 text-sm text-gray-500">
                    URL должен возвращать текстовый список прокси, по одной на строку
                  </p>
                </div>

                <!-- Google Docs -->
                <div v-if="activeImportTab === 'gdocs'">
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Ссылка на Google Документ
                  </label>
                  <input
                    v-model="googleDocUrl"
                    type="url"
                    class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    placeholder="https://docs.google.com/document/d/..."
                  >
                  <p class="mt-2 text-sm text-gray-500">
                    Документ должен быть доступен для просмотра всем, у кого есть ссылка
                  </p>
                </div>

                <!-- Google Sheets -->
                <div v-if="activeImportTab === 'gsheets'">
                  <div class="space-y-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-2">
                        Ссылка на Google Таблицу
                      </label>
                      <input
                        v-model="googleSheetsUrl"
                        type="url"
                        class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                        placeholder="https://docs.google.com/spreadsheets/d/..."
                      >
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-2">
                        Название листа (опционально)
                      </label>
                      <input
                        v-model="sheetName"
                        type="text"
                        class="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                        placeholder="Лист1"
                      >
                    </div>
                  </div>
                  <p class="mt-2 text-sm text-gray-500">
                    Таблица должна быть доступна для просмотра всем, у кого есть ссылка
                  </p>
                </div>
              </div>

              <!-- Результат импорта -->
              <div v-if="importResult" class="mt-6">
                <div
                  :class="[
                    importResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200',
                    'border rounded-md p-4'
                  ]"
                >
                  <div class="flex">
                    <CheckCircleIcon
                      v-if="importResult.success"
                      class="h-5 w-5 text-green-400"
                    />
                    <ExclamationTriangleIcon
                      v-else
                      class="h-5 w-5 text-red-400"
                    />
                    <div class="ml-3">
                      <h3
                        :class="[
                          importResult.success ? 'text-green-800' : 'text-red-800',
                          'text-sm font-medium'
                        ]"
                      >
                        {{ importResult.success ? 'Импорт завершен' : 'Ошибка импорта' }}
                      </h3>
                      <div
                        :class="[
                          importResult.success ? 'text-green-700' : 'text-red-700',
                          'mt-2 text-sm'
                        ]"
                      >
                        <div v-if="importResult.success">
                          <p>Всего обработано: {{ importResult.total }}</p>
                          <p>Успешно импортировано: {{ importResult.successful }}</p>
                          <p v-if="importResult.failed > 0">Ошибок: {{ importResult.failed }}</p>
                        </div>
                        <div v-else>
                          <p>{{ importResult.error }}</p>
                        </div>
                        <div v-if="importResult.errors && importResult.errors.length > 0" class="mt-2">
                          <details>
                            <summary class="cursor-pointer text-sm font-medium">
                              Показать детали ошибок ({{ importResult.errors.length }})
                            </summary>
                            <div class="mt-2 space-y-1">
                              <p
                                v-for="(error, index) in importResult.errors.slice(0, 10)"
                                :key="index"
                                class="text-xs"
                              >
                                {{ error }}
                              </p>
                              <p v-if="importResult.errors.length > 10" class="text-xs">
                                ... и еще {{ importResult.errors.length - 10 }} ошибок
                              </p>
                            </div>
                          </details>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Действия -->
              <div class="mt-6 flex justify-end space-x-3">
                <button
                  @click="$emit('close')"
                  class="btn-secondary"
                >
                  Отмена
                </button>
                <button
                  @click="importProxies"
                  :disabled="importing || !canImport"
                  class="btn-primary"
                >
                  {{ importing ? 'Импорт...' : 'Импортировать' }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>

  <!-- Модальное окно справки по форматам -->
  <ProxyFormatsHelpModal
    :is-open="showFormatsHelp"
    @close="showFormatsHelp = false"
  />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import {
  XMarkIcon,
  DocumentTextIcon,
  UserIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PencilSquareIcon,
  LinkIcon,
  DocumentIcon,
  TableCellsIcon,
  CloudArrowUpIcon
} from '@heroicons/vue/24/outline'
import { api } from '@/api'
import ProxyFormatsHelpModal from './ProxyFormatsHelpModal.vue'

interface Props {
  isOpen: boolean
  domainId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  success: []
}>()

// Табы методов импорта
const importTabs = [
  { key: 'manual', name: 'Ручной ввод', icon: PencilSquareIcon },
  { key: 'file', name: 'Файл', icon: CloudArrowUpIcon },
  { key: 'url', name: 'URL', icon: LinkIcon },
  { key: 'gdocs', name: 'Google Docs', icon: DocumentIcon },
  { key: 'gsheets', name: 'Google Sheets', icon: TableCellsIcon },
]

// State
const selectedProxyType = ref<'warmup' | 'parsing'>('warmup')
const activeImportTab = ref('manual')
const importing = ref(false)
const showFormatsHelp = ref(false)
const importResult = ref<any>(null)

// Данные для разных методов импорта
const manualProxies = ref('')
const selectedFile = ref<File | null>(null)
const proxyUrl = ref('')
const googleDocUrl = ref('')
const googleSheetsUrl = ref('')
const sheetName = ref('')

// Computed
const canImport = computed(() => {
  switch (activeImportTab.value) {
    case 'manual':
      return manualProxies.value.trim().length > 0
    case 'file':
      return selectedFile.value !== null
    case 'url':
      return proxyUrl.value.trim().length > 0
    case 'gdocs':
      return googleDocUrl.value.trim().length > 0
    case 'gsheets':
      return googleSheetsUrl.value.trim().length > 0
    default:
      return false
  }
})

// Methods
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

const importProxies = async () => {
  importing.value = true
  importResult.value = null

  try {
    let response

    switch (activeImportTab.value) {
      case 'manual':
        response = await api.post('/proxies/import/manual', {
          domain_id: props.domainId,
          proxy_type: selectedProxyType.value,
          proxy_text: manualProxies.value
        })
        break

      case 'file':
        if (!selectedFile.value) return

        const formData = new FormData()
        formData.append('domain_id', props.domainId)
        formData.append('proxy_type', selectedProxyType.value)
        formData.append('file', selectedFile.value)

        response = await api.post('/proxies/import/file', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        break

      case 'url':
        response = await api.post('/proxies/import/url', {
          domain_id: props.domainId,
          proxy_type: selectedProxyType.value,
          url: proxyUrl.value
        })
        break

      case 'gdocs':
        const gdocsFormData = new FormData()
        gdocsFormData.append('domain_id', props.domainId)
        gdocsFormData.append('proxy_type', selectedProxyType.value)
        gdocsFormData.append('google_doc_url', googleDocUrl.value)

        response = await api.post('/proxies/import/google-doc', gdocsFormData)
        break

      case 'gsheets':
        const gsheetsFormData = new FormData()
        gsheetsFormData.append('domain_id', props.domainId)
        gsheetsFormData.append('proxy_type', selectedProxyType.value)
        gsheetsFormData.append('google_sheets_url', googleSheetsUrl.value)
        if (sheetName.value) {
          gsheetsFormData.append('sheet_name', sheetName.value)
        }

        response = await api.post('/proxies/import/google-sheets', gsheetsFormData)
        break

      default:
        throw new Error('Неизвестный метод импорта')
    }

    importResult.value = response.data

    if (response.data.success) {
      // Очищаем формы после успешного импорта
      resetForms()

      // Ждем немного и закрываем модальное окно
      setTimeout(() => {
        emit('success')
      }, 2000)
    }

  } catch (error: any) {
    console.error('Ошибка импорта прокси:', error)
    importResult.value = {
      success: false,
      error: error.response?.data?.detail || 'Произошла ошибка при импорте'
    }
  } finally {
    importing.value = false
  }
}

const resetForms = () => {
  manualProxies.value = ''
  selectedFile.value = null
  proxyUrl.value = ''
  googleDocUrl.value = ''
  googleSheetsUrl.value = ''
  sheetName.value = ''
  importResult.value = null
}

// Сброс результата при смене таба
const resetResult = () => {
  importResult.value = null
}

// Watches
import { watch } from 'vue'

watch(activeImportTab, resetResult)
watch(() => props.isOpen, (isOpen) => {
  if (!isOpen) {
    resetForms()
  }
})
</script>
