<template>
    <Modal
        :isOpen="isOpen"
        title="Быстрый парсинг"
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
                        placeholder="Введите поисковый запрос"
                        @input="clearError('keyword')"
                    />
                    <p v-if="errors.keyword" class="mt-1 text-sm text-red-600">
                        {{ errors.keyword }}
                    </p>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label for="pages" class="block text-sm font-medium text-gray-700">
                            Количество страниц
                        </label>
                        <select
                            id="pages"
                            v-model.number="form.pages"
                            class="input mt-1"
                        >
                            <option :value="1">1 страница</option>
                            <option :value="3">3 страницы</option>
                            <option :value="5">5 страниц</option>
                            <option :value="10">10 страниц</option>
                            <option :value="20">20 страниц</option>
                        </select>
                    </div>

                    <div>
                        <label for="region" class="block text-sm font-medium text-gray-700">
                            Регион
                        </label>
                        <select
                            id="region"
                            v-model="form.regionCode"
                            class="input mt-1"
                        >
                            <option value="213">Москва</option>
                            <option value="2">Санкт-Петербург</option>
                            <option value="54">Екатеринбург</option>
                            <option value="65">Новосибирск</option>
                            <option value="35">Краснодар</option>
                        </select>
                    </div>
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
                <ComputerDesktopIcon class="mr-1 h-4 w-4"/>
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
                <DevicePhoneMobileIcon class="mr-1 h-4 w-4"/>
                Мобильный
              </span>
                        </label>
                    </div>
                </div>

                <!-- Cost calculation -->
                <div v-if="estimatedCost" class="rounded-md bg-blue-50 p-4">
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-blue-700">Ориентировочная стоимость:</span>
                        <span class="text-sm font-semibold text-blue-900">
              {{ formatCurrency(estimatedCost) }}
            </span>
                    </div>
                </div>
            </div>

            <Alert
                v-if="tasksStore.error"
                type="error"
                :message="tasksStore.error"
                class="mt-4"
                dismissible
                @dismiss="tasksStore.error = null"
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
                :disabled="tasksStore.loading"
            >
                <Spinner v-if="tasksStore.loading" class="mr-2 h-4 w-4"/>
                Создать задачу
            </button>
        </template>
    </Modal>
</template>

<script setup lang="ts">
import {reactive, ref, computed, watch} from 'vue'
import {ComputerDesktopIcon, DevicePhoneMobileIcon} from '@heroicons/vue/24/outline'
import {useTasksStore} from '@/stores/tasks'
import {useBillingStore} from '@/stores/billing'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
    isOpen: boolean
}

interface Emits {
    (e: 'close'): void

    (e: 'success', taskId: string): void
}

// defineProps<Props>()
// const emit = defineEmits<Emits>()

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const tasksStore = useTasksStore()
const billingStore = useBillingStore()

const form = reactive({
    keyword: '',
    pages: 10,
    regionCode: '213',
    deviceType: 'desktop'
})

const errors = ref<Record<string, string>>({})
const estimatedCost = ref<number>(0)

const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 2
    }).format(amount)
}

const validateForm = () => {
    errors.value = {}

    if (!form.keyword.trim()) {
        errors.value.keyword = 'Ключевое слово обязательно'
    }

    return Object.keys(errors.value).length === 0
}

const clearError = (field: string) => {
    if (errors.value[field]) {
        delete errors.value[field]
    }
}

const calculateCost = async () => {
    try {
        const result = await billingStore.calculateCheckCost(1)
        estimatedCost.value = result.total_cost
    } catch (error) {
        console.error('Error calculating cost:', error)
    }
}

const handleSubmit = async () => {
    if (!validateForm()) {
        return
    }

    try {
        const result = await tasksStore.createParseTask(
            form.keyword.trim(),
            form.deviceType,
            form.pages,
            form.regionCode
        )

        // Сбрасываем форму
        form.keyword = ''
        form.pages = 10
        form.regionCode = '213'
        form.deviceType = 'desktop'
        errors.value = {}

        emit('success', result.task_id)
    } catch (error) {
        console.error('Error creating parse task:', error)
    }
}

// Рассчитываем стоимость при открытии модального окна
watch(() => props.isOpen, (isOpen) => {
    if (isOpen) {
        calculateCost()
    }
})
</script>
