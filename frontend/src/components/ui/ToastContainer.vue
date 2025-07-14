<!-- frontend/src/components/ui/ToastContainer.vue -->
<template>
    <Teleport to="body">
        <div class="fixed top-4 right-4 z-50 space-y-2">
            <TransitionGroup
                name="toast"
                tag="div"
                class="space-y-2"
            >
                <div
                    v-for="toast in toasts"
                    :key="toast.id"
                    :class="getToastClasses(toast.type)"
                    class="max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden"
                >
                    <div class="p-4">
                        <div class="flex items-start">
                            <div class="flex-shrink-0">
                                <component :is="getIcon(toast.type)"
                                           :class="getIconClasses(toast.type)" class="h-6 w-6"/>
                            </div>
                            <div class="ml-3 w-0 flex-1 pt-0.5">
                                <p class="text-sm font-medium text-gray-900">
                                    {{ toast.title }}
                                </p>
                                <p v-if="toast.message" class="mt-1 text-sm text-gray-500">
                                    {{ toast.message }}
                                </p>
                            </div>
                            <div class="ml-4 flex-shrink-0 flex">
                                <button
                                    @click="removeToast(toast.id)"
                                    class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                                >
                                    <span class="sr-only">Закрыть</span>
                                    <XMarkIcon class="h-5 w-5"/>
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Progress bar для неперсистентных toast -->
                    <div
                        v-if="!toast.persistent && toast.duration !== 0"
                        class="h-1 bg-gray-100 overflow-hidden"
                    >
                        <div
                            :class="getProgressBarClasses(toast.type)"
                            class="h-full progress-bar"
                            :style="{ animationDuration: `${toast.duration || 5000}ms` }"
                        ></div>
                    </div>
                </div>
            </TransitionGroup>
        </div>
    </Teleport>
</template>

<script setup lang="ts">
import {computed} from 'vue'
import {useToast} from '@/composables/useToast'
import {
    CheckCircleIcon,
    ExclamationTriangleIcon,
    InformationCircleIcon,
    XCircleIcon,
    XMarkIcon
} from '@heroicons/vue/24/outline'

const {toasts, removeToast} = useToast()

const getIcon = (type: string) => {
    const icons = {
        success: CheckCircleIcon,
        error: XCircleIcon,
        warning: ExclamationTriangleIcon,
        info: InformationCircleIcon
    }
    return icons[type] || InformationCircleIcon
}

const getIconClasses = (type: string) => {
    const classes = {
        success: 'text-green-400',
        error: 'text-red-400',
        warning: 'text-yellow-400',
        info: 'text-blue-400'
    }
    return classes[type] || 'text-blue-400'
}

const getToastClasses = (type: string) => {
    const classes = {
        success: 'border-l-4 border-green-400',
        error: 'border-l-4 border-red-400',
        warning: 'border-l-4 border-yellow-400',
        info: 'border-l-4 border-blue-400'
    }
    return classes[type] || 'border-l-4 border-blue-400'
}

const getProgressBarClasses = (type: string) => {
    const classes = {
        success: 'bg-green-400',
        error: 'bg-red-400',
        warning: 'bg-yellow-400',
        info: 'bg-blue-400'
    }
    return classes[type] || 'bg-blue-400'
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
    transition: all 0.3s ease;
}

.toast-enter-from {
    opacity: 0;
    transform: translateX(100%);
}

.toast-leave-to {
    opacity: 0;
    transform: translateX(100%);
}

.progress-bar {
    animation: progress linear forwards;
    transform-origin: left;
}

@keyframes progress {
    from {
        transform: scaleX(1);
    }
    to {
        transform: scaleX(0);
    }
}
</style>
