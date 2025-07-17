<!-- frontend/src/components/strategies/ProfileNurtureTasksModal.vue -->
<template>
    <div class="fixed inset-0 z-50 overflow-y-auto">
        <div
            class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <!-- Overlay -->
            <div
                class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                @click="$emit('close')"
            ></div>

            <!-- Modal -->
            <div
                class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
                <div class="bg-white px-4 pt-5 pb-4 sm:p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-medium text-gray-900">
                            Мониторинг задач нагула
                        </h3>
                        <button
                            @click="$emit('close')"
                            class="text-gray-400 hover:text-gray-500"
                        >
                            <XMarkIcon class="h-6 w-6"/>
                        </button>
                    </div>

                    <!-- ВСТРАИВАЕМ существующий компонент -->
                    <ProfileNurtureTasksMonitor
                        :strategy-id="strategyId"
                        class="max-h-96 overflow-y-auto"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {XMarkIcon} from '@heroicons/vue/24/outline'
import ProfileNurtureTasksMonitor from './ProfileNurtureTasksMonitor.vue'

interface Props {
    strategyId: string
}

defineProps<Props>()
defineEmits<{
    close: []
}>()
</script>
