<template>
    <Modal
        :isOpen="isOpen"
        title="Удалить домен"
        @close="$emit('close')"
    >
        <div class="space-y-4">
            <div class="flex items-center p-4 bg-red-50 rounded-lg">
                <ExclamationTriangleIcon class="h-8 w-8 text-red-600 mr-3 flex-shrink-0"/>
                <div>
                    <h3 class="text-sm font-medium text-red-800">
                        Внимание! Это действие нельзя отменить
                    </h3>
                    <p class="text-sm text-red-700 mt-1">
                        Все связанные ключевые слова и их история также будут удалены
                    </p>
                </div>
            </div>

            <div v-if="domain" class="bg-gray-50 p-4 rounded-lg">
                <h4 class="text-sm font-medium text-gray-900 mb-2">
                    Информация о домене:
                </h4>
                <dl class="grid grid-cols-1 gap-2 text-sm">
                    <div class="flex justify-between">
                        <dt class="text-gray-500">Домен:</dt>
                        <dd class="font-medium text-gray-900">{{ domain.domain }}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-gray-500">Регион:</dt>
                        <dd class="font-medium text-gray-900">
                            {{ domain.region?.name || 'Не указан' }}
                            <span v-if="domain.region" class="text-gray-500 ml-1">
                ({{ domain.region.code }})
              </span>
                        </dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-gray-500">Ключевых слов:</dt>
                        <dd class="font-medium text-gray-900">{{ domain.keywords_count }}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-gray-500">Создан:</dt>
                        <dd class="font-medium text-gray-900">{{
                                formatDate(domain.created_at)
                            }}
                        </dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-gray-500">Статус:</dt>
                        <dd class="flex items-center">
              <span
                  :class="[
                  'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                  domain.is_verified
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                ]"
              >
                <CheckIcon v-if="domain.is_verified" class="mr-1 h-3 w-3"/>
                {{ domain.is_verified ? 'Подтвержден' : 'Не подтвержден' }}
              </span>
                        </dd>
                    </div>
                </dl>
            </div>

            <div class="bg-yellow-50 p-4 rounded-lg">
                <div class="flex items-start">
                    <ExclamationTriangleIcon
                        class="h-5 w-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5"/>
                    <div>
                        <h4 class="text-sm font-medium text-yellow-800">
                            Что будет удалено:
                        </h4>
                        <ul class="text-sm text-yellow-700 mt-1 space-y-1">
                            <li>• Домен {{ domain?.domain }}</li>
                            <li>• Все {{ domain?.keywords_count || 0 }} ключевых слов</li>
                            <li>• История проверок позиций</li>
                            <li>• Настройки домена</li>
                            <li>• Связанные задачи парсинга</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="space-y-3">
                <p class="text-sm text-gray-700">
                    Чтобы подтвердить удаление, введите название домена:
                </p>
                <input
                    v-model="confirmationInput"
                    type="text"
                    class="input w-full"
                    :class="{ 'border-red-500': confirmationError }"
                    :placeholder="domain?.domain || ''"
                    @input="clearConfirmationError"
                />
                <p v-if="confirmationError" class="text-sm text-red-600">
                    {{ confirmationError }}
                </p>
            </div>

            <Alert
                v-if="domainsStore.error"
                type="error"
                :message="domainsStore.error"
                class="mt-4"
                dismissible
                @dismiss="domainsStore.error = null"
            />
        </div>

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
                class="btn-danger ml-3"
                @click="handleDelete"
                :disabled="!canDelete || domainsStore.loading"
            >
                <Spinner v-if="domainsStore.loading" class="mr-2 h-4 w-4"/>
                Удалить домен
            </button>
        </template>
    </Modal>
</template>

<script setup lang="ts">
import {ref, computed, watch} from 'vue'
import {ExclamationTriangleIcon, CheckIcon} from '@heroicons/vue/24/outline'
import {useDomainsStore, type Domain} from '@/stores/domains'
import Modal from '@/components/ui/Modal.vue'
import Alert from '@/components/ui/Alert.vue'
import Spinner from '@/components/ui/Spinner.vue'

interface Props {
    isOpen: boolean
    domain: Domain | null
}

interface Emits {
    (e: 'close'): void

    (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const domainsStore = useDomainsStore()

const confirmationInput = ref('')
const confirmationError = ref('')

const canDelete = computed(() => {
    return props.domain && confirmationInput.value.trim().toLowerCase() === props.domain.domain.toLowerCase()
})

const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(dateString))
}

const clearConfirmationError = () => {
    confirmationError.value = ''
}

const handleDelete = async () => {
    if (!props.domain) {
        return
    }

    if (confirmationInput.value.trim().toLowerCase() !== props.domain.domain.toLowerCase()) {
        confirmationError.value = 'Введите точное название домена для подтверждения'
        return
    }

    try {
        await domainsStore.deleteDomain(props.domain.id)

        // Сбрасываем форму
        confirmationInput.value = ''
        confirmationError.value = ''

        emit('success')
    } catch (error) {
        console.error('Error deleting domain:', error)
    }
}

// Сбрасываем форму при открытии модального окна
watch(() => props.isOpen, (isOpen) => {
    if (isOpen) {
        confirmationInput.value = ''
        confirmationError.value = ''
    }
})
</script>
