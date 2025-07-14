<!-- frontend/src/components/proxy/ProxyFormatsHelpModal.vue -->
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
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-3xl sm:p-6">
              <!-- Заголовок -->
              <div class="flex items-center justify-between mb-6">
                <DialogTitle as="h3" class="text-lg font-medium text-gray-900">
                  Поддерживаемые форматы прокси
                </DialogTitle>
                <button
                  @click="$emit('close')"
                  class="rounded-md bg-white text-gray-400 hover:text-gray-500"
                >
                  <XMarkIcon class="h-6 w-6" />
                </button>
              </div>

              <!-- Форматы -->
              <div class="space-y-6">
                <div
                  v-for="format in formats"
                  :key="format.format"
                  class="border border-gray-200 rounded-lg p-4"
                >
                  <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                      <div class="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                        <span class="text-primary-600 font-medium text-sm">{{ format.id }}</span>
                      </div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h4 class="text-sm font-medium text-gray-900 mb-1">
                        {{ format.format }}
                      </h4>
                      <p class="text-sm text-gray-600 mb-2">
                        {{ format.description }}
                      </p>
                      <div class="bg-gray-50 rounded-md p-3">
                        <code class="text-sm text-gray-800 font-mono">
                          {{ format.example }}
                        </code>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Примечания -->
              <div class="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
                <div class="flex">
                  <InformationCircleIcon class="h-5 w-5 text-blue-400 flex-shrink-0" />
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-blue-800">
                      Важные примечания
                    </h3>
                    <div class="mt-2 text-sm text-blue-700">
                      <ul class="list-disc list-inside space-y-1">
                        <li>Каждая прокси должна быть на отдельной строке</li>
                        <li>Строки, начинающиеся с #, игнорируются (комментарии)</li>
                        <li>Пустые строки автоматически пропускаются</li>
                        <li>Поддерживаются протоколы: HTTP, HTTPS, SOCKS4, SOCKS5</li>
                        <li>При отсутствии протокола используется HTTP по умолчанию</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Пример файла -->
              <div class="mt-6">
                <h4 class="text-sm font-medium text-gray-900 mb-3">
                  Пример содержимого файла:
                </h4>
                <div class="bg-gray-900 rounded-md p-4 overflow-x-auto">
                  <pre class="text-sm text-green-400 font-mono">{{ exampleFileContent }}</pre>
                </div>
              </div>

              <!-- Действия -->
              <div class="mt-6 flex justify-end">
                <button
                  @click="$emit('close')"
                  class="btn-primary"
                >
                  Понятно
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import { XMarkIcon, InformationCircleIcon } from '@heroicons/vue/24/outline'

interface Props {
  isOpen: boolean
}

defineProps<Props>()
defineEmits<{
  close: []
}>()

const formats = [
  {
    id: '1',
    format: 'protocol://user:password@host:port',
    example: 'http://john:secret123@192.168.1.100:8080',
    description: 'Полный формат с протоколом и авторизацией'
  },
  {
    id: '2',
    format: 'user:password@host:port',
    example: 'john:secret123@192.168.1.100:8080',
    description: 'Формат с авторизацией без указания протокола'
  },
  {
    id: '3',
    format: 'host:port:user:password',
    example: '192.168.1.100:8080:john:secret123',
    description: 'Популярный формат через двоеточия'
  },
  {
    id: '4',
    format: 'host:port@user:password',
    example: '192.168.1.100:8080@john:secret123',
    description: 'Альтернативный формат с символом @'
  },
  {
    id: '5',
    format: 'host:port',
    example: '192.168.1.100:8080',
    description: 'Простой формат без авторизации'
  },
  {
    id: '6',
    format: 'socks5://user:password@host:port',
    example: 'socks5://john:secret123@192.168.1.100:1080',
    description: 'SOCKS5 прокси с авторизацией'
  },
  {
    id: '7',
    format: 'socks5://host:port',
    example: 'socks5://192.168.1.100:1080',
    description: 'SOCKS5 прокси без авторизации'
  }
]

const exampleFileContent = `# Список прокси для проекта
# Формат: различные поддерживаемые варианты

# HTTP прокси с авторизацией
http://user1:pass1@proxy1.example.com:8080
https://user2:pass2@proxy2.example.com:8080

# Формат через двоеточия
192.168.1.100:3128:username:password
10.0.0.50:8080:admin:12345

# Формат с @ разделителем
user:pass@proxy.company.com:8080
192.168.1.200:3128@proxyuser:secretpass

# Прокси без авторизации
proxy-free.example.com:8080
203.0.113.45:3128

# SOCKS5 прокси
socks5://sockuser:sockpass@socks.example.com:1080
socks5://127.0.0.1:9050

# Этот комментарий будет проигнорирован
# Пустые строки тоже игнорируются`
</script>
