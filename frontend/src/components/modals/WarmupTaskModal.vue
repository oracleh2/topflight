<!-- frontend/src/components/modals/WarmupTaskModal.vue -->
<template>
    <div v-if="visible" class="fixed inset-0 z-50 overflow-y-auto">
        <div
            class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="close"/>

            <div
                class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                    <div class="sm:flex sm:items-start">
                        <div
                            class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                            <CpuChipIcon class="h-6 w-6 text-blue-600" aria-hidden="true"/>
                        </div>

                        <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                            <h3 class="text-base font-semibold leading-6 text-gray-900">
                                Создать задачу нагула профиля
                            </h3>

                            <div class="mt-4 space-y-4">
                                <!-- Device Type -->
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-2">
                                        Тип устройства
                                    </label>
                                    <select
                                        v-model="form.deviceType"
                                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                    >
                                        <option value="desktop">Desktop</option>
                                        <option value="mobile">Mobile</option>
                                    </select>
                                </div>

                                <!-- Profile ID (optional) -->
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-2">
                                        ID профиля (опционально)
                                    </label>
                                    <input
                                        v-model="form.profileId"
                                        type="text"
                                        placeholder="Оставьте пустым для создания нового профиля"
                                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                    />
                                    <p class="mt-1 text-sm text-gray-500">
                                        Если не указан, будет создан новый профиль
                                    </p>
                                </div>

                                <!-- Priority -->
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-2">
                                        Приоритет (1-20)
                                    </label>
                                    <input
                                        v-model.number="form.priority"
                                        type="number"
                                        min="1"
                                        max="20"
                                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                    />
                                </div>
                            </div>

                            <!-- Error display -->
                            <div v-if="error" class="mt-4">
                                <div class="rounded-md bg-red-50 p-4">
                                    <div class="flex">
                                        <ExclamationTriangleIcon class="h-5 w-5 text-red-400"
                                                                 aria-hidden="true"/>
                                        <div class="ml-3">
                                            <h3 class="text-sm font-medium text-red-800">
                                                Ошибка
                                            </h3>
                                            <div class="mt-2 text-sm text-red-700">
                                                {{ error }}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                    <button
                        type="button"
                        :disabled="loading"
                        @click="createTask"
                        class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed sm:ml-3 sm:w-auto"
                    >
            <span v-if="loading" class="mr-2">
              <div
                  class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
            </span>
                        {{ loading ? 'Создание...' : 'Создать задачу' }}
                    </button>

                    <button
                        type="button"
                        @click="close"
                        class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                    >
                        Отмена
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, reactive, watch} from 'vue'
import {CpuChipIcon, ExclamationTriangleIcon} from '@heroicons/vue/24/outline'
import {useTasksStore} from '@/stores/tasks'

interface Props {
    visible: boolean
}

interface Emits {
    (e: 'update:visible', value: boolean): void

    (e: 'created'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const tasksStore = useTasksStore()

const form = reactive({
    deviceType: 'desktop',
    profileId: '',
    priority: 2
})

const loading = ref(false)
const error = ref<string | null>(null)

// Reset form when modal opens
watch(() => props.visible, (visible) => {
    if (visible) {
        form.deviceType = 'desktop'
        form.profileId = ''
        form.priority = 2
        error.value = null
    }
})

const createTask = async () => {
    if (loading.value) return

    try {
        loading.value = true
        error.value = null

        await tasksStore.createWarmupTask(
            form.deviceType,
            form.profileId || undefined,
            form.priority
        )

        emit('created')
        close()
    } catch (err: any) {
        error.value = err.message || 'Произошла ошибка при создании задачи'
    } finally {
        loading.value = false
    }
}

const close = () => {
    if (!loading.value) {
        emit('update:visible', false)
    }
}
</script>
