// frontend/src/composables/useNotifications.ts

import {ref} from 'vue'

export interface Notification {
    id: string
    message: string
    type: 'success' | 'error' | 'warning' | 'info'
    duration?: number
}

const notifications = ref<Notification[]>([])

export const useNotifications = () => {
    const addNotification = (notification: Omit<Notification, 'id'>) => {
        const id = Date.now().toString()
        const newNotification: Notification = {
            id,
            duration: 5000,
            ...notification,
        }

        notifications.value.push(newNotification)

        // Auto remove after duration
        if (newNotification.duration && newNotification.duration > 0) {
            setTimeout(() => {
                removeNotification(id)
            }, newNotification.duration)
        }

        return id
    }

    const removeNotification = (id: string) => {
        const index = notifications.value.findIndex(n => n.id === id)
        if (index > -1) {
            notifications.value.splice(index, 1)
        }
    }

    const showNotification = (message: string, type: Notification['type'] = 'info', duration?: number) => {
        return addNotification({message, type, duration})
    }

    const clearAllNotifications = () => {
        notifications.value = []
    }

    return {
        notifications,
        addNotification,
        removeNotification,
        showNotification,
        clearAllNotifications,
    }
}
