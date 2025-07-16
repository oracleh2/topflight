<!-- frontend/src/components/common/NotificationContainer.vue -->

<template>
    <div
        v-if="notifications.length > 0"
        class="fixed top-4 right-4 z-50 space-y-2"
    >
        <div
            v-for="notification in notifications"
            :key="notification.id"
            :class="[
        'max-w-sm w-full shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden',
        getNotificationClass(notification.type)
      ]"
        >
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <CheckCircleIcon v-if="notification.type === 'success'"
                                         class="h-6 w-6 text-green-400"/>
                        <ExclamationTriangleIcon v-else-if="notification.type === 'warning'"
                                                 class="h-6 w-6 text-yellow-400"/>
                        <XCircleIcon v-else-if="notification.type === 'error'"
                                     class="h-6 w-6 text-red-400"/>
                        <InformationCircleIcon v-else class="h-6 w-6 text-blue-400"/>
                    </div>
                    <div class="ml-3 w-0 flex-1 pt-0.5">
                        <p :class="[
              'text-sm font-medium',
              getTextClass(notification.type)
            ]">
                            {{ notification.message }}
                        </p>
                    </div>
                    <div class="ml-4 flex-shrink-0 flex">
                        <button
                            @click="removeNotification(notification.id)"
                            :class="[
                'inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2',
                getButtonClass(notification.type)
              ]"
                        >
                            <span class="sr-only">Закрыть</span>
                            <XMarkIcon class="h-5 w-5"/>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {useNotifications} from '@/composables/useNotifications'
import {
    CheckCircleIcon,
    ExclamationTriangleIcon,
    XCircleIcon,
    InformationCircleIcon,
    XMarkIcon,
} from '@heroicons/vue/24/outline'

const {notifications, removeNotification} = useNotifications()

const getNotificationClass = (type: string) => {
    switch (type) {
        case 'success':
            return 'bg-green-50'
        case 'warning':
            return 'bg-yellow-50'
        case 'error':
            return 'bg-red-50'
        default:
            return 'bg-blue-50'
    }
}

const getTextClass = (type: string) => {
    switch (type) {
        case 'success':
            return 'text-green-800'
        case 'warning':
            return 'text-yellow-800'
        case 'error':
            return 'text-red-800'
        default:
            return 'text-blue-800'
    }
}

const getButtonClass = (type: string) => {
    switch (type) {
        case 'success':
            return 'text-green-400 hover:text-green-500 focus:ring-green-500'
        case 'warning':
            return 'text-yellow-400 hover:text-yellow-500 focus:ring-yellow-500'
        case 'error':
            return 'text-red-400 hover:text-red-500 focus:ring-red-500'
        default:
            return 'text-blue-400 hover:text-blue-500 focus:ring-blue-500'
    }
}
</script>
