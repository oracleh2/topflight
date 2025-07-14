<!-- frontend/src/components/proxy/ProxyManagerModal.vue -->
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
                <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"/>
            </TransitionChild>

            <div class="fixed inset-0 z-10 overflow-y-auto">
                <div
                    class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <TransitionChild
                        as="template"
                        enter="ease-out duration-300"
                        enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
                        enter-to="opacity-100 translate-y-0 sm:scale-100"
                        leave="ease-in duration-200"
                        leave-from="opacity-100 translate-y-0 sm:scale-100"
                        leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
                    >
                        <DialogPanel
                            class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-6xl sm:p-0">
                            <!-- Заголовок -->
                            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                <div class="flex items-center justify-between">
                                    <DialogTitle as="h3" class="text-lg font-medium text-gray-900">
                                        Управление прокси
                                    </DialogTitle>
                                    <button
                                        @click="$emit('close')"
                                        class="rounded-md bg-white text-gray-400 hover:text-gray-500"
                                    >
                                        <XMarkIcon class="h-6 w-6"/>
                                    </button>
                                </div>
                            </div>

                            <!-- Контент -->
                            <div class="px-4 pb-4 sm:px-6">
                                <ProxyManager :domain-id="domainId"/>
                            </div>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>
</template>

<script setup lang="ts">
import {Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot,} from '@headlessui/vue'
import {XMarkIcon} from '@heroicons/vue/24/outline'
import ProxyManager from './ProxyManager.vue'

interface Props {
    isOpen: boolean
    domainId: string
}

defineProps<Props>()
defineEmits<{
    close: []
    updated: []
}>()
</script>
