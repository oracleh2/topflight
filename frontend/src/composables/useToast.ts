// frontend/src/composables/useToast.ts
import {ref, reactive} from 'vue'

export interface Toast {
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message?: string
    duration?: number
    persistent?: boolean
}

interface ToastOptions {
    title: string
    message?: string
    duration?: number
    persistent?: boolean
}

const toasts = ref<Toast[]>([])
const defaultDuration = 5000

let toastIdCounter = 0

const generateId = (): string => {
    return `toast-${++toastIdCounter}-${Date.now()}`
}

const addToast = (toast: Toast): void => {
    toasts.value.push(toast)

    // Автоматически удаляем toast через указанное время, если он не persistent
    if (!toast.persistent && toast.duration !== 0) {
        setTimeout(() => {
            removeToast(toast.id)
        }, toast.duration || defaultDuration)
    }
}

const removeToast = (id: string): void => {
    const index = toasts.value.findIndex(toast => toast.id === id)
    if (index > -1) {
        toasts.value.splice(index, 1)
    }
}

const clearAllToasts = (): void => {
    toasts.value = []
}

export const useToast = () => {
    const showToast = (type: Toast['type'], options: ToastOptions): string => {
        const toast: Toast = {
            id: generateId(),
            type,
            title: options.title,
            message: options.message,
            duration: options.duration,
            persistent: options.persistent
        }

        addToast(toast)
        return toast.id
    }

    const showSuccess = (options: ToastOptions): string => {
        return showToast('success', options)
    }

    const showError = (options: ToastOptions): string => {
        return showToast('error', options)
    }

    const showWarning = (options: ToastOptions): string => {
        return showToast('warning', options)
    }

    const showInfo = (options: ToastOptions): string => {
        return showToast('info', options)
    }

    // Упрощенные методы для быстрого использования
    const success = (title: string, message?: string, duration?: number): string => {
        return showSuccess({title, message, duration})
    }

    const error = (title: string, message?: string, duration?: number): string => {
        return showError({title, message, duration})
    }

    const warning = (title: string, message?: string, duration?: number): string => {
        return showWarning({title, message, duration})
    }

    const info = (title: string, message?: string, duration?: number): string => {
        return showInfo({title, message, duration})
    }

    return {
        // Состояние
        toasts: toasts.value,

        // Методы управления
        showToast,
        showSuccess,
        showError,
        showWarning,
        showInfo,

        // Упрощенные методы
        success,
        error,
        warning,
        info,

        // Утилиты
        removeToast,
        clearAllToasts
    }
}
