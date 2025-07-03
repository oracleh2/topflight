<template>
  <Modal
    :isOpen="isOpen"
    title="Добавить домен"
    @close="$emit('close')"
  >
    <form @submit.prevent="handleSubmit">
      <div class="space-y-4">
        <div>
          <label for="domain" class="block text-sm font-medium text-gray-700">
            Домен
          </label>
          <input
            id="domain"
            v-model="form.domain"
            type="text"
            class="input mt-1"
            :class="{ 'border-red-500': errors.domain }"
            placeholder="example.com"
            @input="clearError('domain')"
          />
          <p v-if="errors.domain" class="mt-1 text-sm text-red-600">
            {{ errors.domain }}
          </p>
          <p class="mt-1 text-xs text-gray-500">
            Введите домен без http:// и www.
          </p>
        </div>
      </div>

      <Alert
        v-if="domainsStore.error"
        type="error"
        :message="domainsStore.error"
        class="mt-4"
        dismissible
        @dismiss="domainsStore.error = null"
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
        :disabled="domainsStore.loading"
      >
        <Spinner v-if="domainsStore.loading" class="mr-2 h-4 w-4" />
        Добавить
      </button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useDomainsStore } from '@/stores/domains'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
  isOpen: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'success', domainId: string): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const domainsStore = useDomainsStore()

const form = reactive({
  domain: ''
})

const errors = ref<Record<string, string>>({})

const validateForm = () => {
  errors.value = {}

  if (!form.domain.trim()) {
    errors.value.domain = 'Домен обязателен'
    return false
  }

  // Простая валидация домена
  const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.([a-zA-Z]{2,}\.)*[a-zA-Z]{2,}$/
  const cleanDomain = form.domain.trim().toLowerCase()
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .replace(/\/$/, '')

  if (!domainRegex.test(cleanDomain)) {
    errors.value.domain = 'Некорректный формат домена'
    return false
  }

  form.domain = cleanDomain
  return true
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
    const result = await domainsStore.addDomain(form.domain)

    // Сбрасываем форму
    form.domain = ''
    errors.value = {}

    emit('success', result.domain_id)
  } catch (error) {
    console.error('Error adding domain:', error)
  }
}
</script>
