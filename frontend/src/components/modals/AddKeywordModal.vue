<template>
  <Modal
    :isOpen="isOpen"
    title="Добавить ключевое слово"
    panel-class="max-w-lg"
    @close="$emit('close')"
  >
    <form @submit.prevent="handleSubmit">
      <div class="space-y-4">
        <div>
          <label for="keyword" class="block text-sm font-medium text-gray-700">
            Ключевое слово
          </label>
          <input
            id="keyword"
            v-model="form.keyword"
            type="text"
            class="input mt-1"
            :class="{ 'border-red-500': errors.keyword }"
            placeholder="Введите ключевое слово"
            @input="clearError('keyword')"
          />
          <p v-if="errors.keyword" class="mt-1 text-sm text-red-600">
            {{ errors.keyword }}
          </p>
        </div>

        <div>
          <label for="region" class="block text-sm font-medium text-gray-700">
            Регион
          </label>
          <select
            id="region"
            v-model="form.regionId"
            class="input mt-1"
            :class="{ 'border-red-500': errors.regionId }"
            @change="clearError('regionId')"
          >
            <option value="">Выберите регион</option>
            <option
              v-for="region in domainsStore.regions"
              :key="region.id"
              :value="region.id"
            >
              {{ region.name }} ({{ region.code }})
            </option>
          </select>
          <p v-if="errors.regionId" class="mt-1 text-sm text-red-600">
            {{ errors.regionId }}
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700">
            Тип устройства
          </label>
          <div class="mt-2 space-y-2">
            <label class="flex items-center">
              <input
                v-model="form.deviceType"
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
                v-model="form.deviceType"
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

        <div>
          <label for="frequency" class="block text-sm font-medium text-gray-700">
            Частота проверки
          </label>
          <select
            id="frequency"
            v-model="form.checkFrequency"
            class="input mt-1"
          >
            <option value="daily">Ежедневно</option>
            <option value="weekly">Еженедельно</option>
            <option value="monthly">Ежемесячно</option>
          </select>
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
import { reactive, ref, onMounted } from 'vue'
import { ComputerDesktopIcon, DevicePhoneMobileIcon } from '@heroicons/vue/24/outline'
import { useDomainsStore } from '@/stores/domains'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
  isOpen: boolean
  domainId: string
}

interface Emits {
  (e: 'close'): void
  (e: 'success'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const domainsStore = useDomainsStore()

const form = reactive({
  keyword: '',
  regionId: '',
  deviceType: 'desktop',
  checkFrequency: 'daily'
})

const errors = ref<Record<string, string>>({})

const validateForm = () => {
  errors.value = {}

  if (!form.keyword.trim()) {
    errors.value.keyword = 'Ключевое слово обязательно'
  }

  if (!form.regionId) {
    errors.value.regionId = 'Регион обязателен'
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
    await domainsStore.addKeyword(
      props.domainId,
      form.keyword.trim(),
      form.regionId,
      form.deviceType
    )

    // Сбрасываем форму
    form.keyword = ''
    form.regionId = ''
    form.deviceType = 'desktop'
    form.checkFrequency = 'daily'
    errors.value = {}

    emit('success')
  } catch (error) {
    console.error('Error adding keyword:', error)
  }
}

onMounted(() => {
  // Загружаем регионы если они не загружены
  if (!domainsStore.regions.length) {
    domainsStore.fetchRegions()
  }
})
</script>
