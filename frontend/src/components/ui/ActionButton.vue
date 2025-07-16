<!-- frontend/src/components/ui/ActionButton.vue -->

<template>
    <button
        @click="handleClick"
        :disabled="loading || disabled"
        :class="[
      'inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md',
      'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
      'transition-colors duration-200',
      {
        'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary' && !loading && !disabled,
        'bg-gray-600 text-white hover:bg-gray-700': variant === 'secondary' && !loading && !disabled,
        'bg-green-600 text-white hover:bg-green-700': variant === 'success' && !loading && !disabled,
        'bg-red-600 text-white hover:bg-red-700': variant === 'danger' && !loading && !disabled,
        'bg-gray-300 text-gray-500 cursor-not-allowed': loading || disabled,
      }
    ]"
    >
        <!-- Спиннер загрузки -->
        <svg
            v-if="loading"
            class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
        >
            <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
            ></circle>
            <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
        </svg>

        <!-- Иконка (если не загружается) -->
        <component
            :is="icon"
            v-else-if="icon"
            class="w-4 h-4 mr-2"
            aria-hidden="true"
        />

        <!-- Текст кнопки -->
        <span>{{ loading ? loadingText : text }}</span>
    </button>
</template>

<script>
import {PlayIcon, ArrowPathIcon, PlusIcon} from '@heroicons/vue/24/outline'

export default {
    name: 'ActionButton',
    components: {
        PlayIcon,
        ArrowPathIcon,
        PlusIcon
    },
    props: {
        text: {
            type: String,
            default: 'Создать задачи'
        },
        loadingText: {
            type: String,
            default: 'Создание...'
        },
        variant: {
            type: String,
            default: 'primary',
            validator: (value) => ['primary', 'secondary', 'success', 'danger'].includes(value)
        },
        loading: {
            type: Boolean,
            default: false
        },
        disabled: {
            type: Boolean,
            default: false
        },
        icon: {
            type: [String, Object],
            default: 'PlusIcon'
        }
    },
    emits: ['click'],
    setup(props, {emit}) {
        const handleClick = () => {
            if (!props.loading && !props.disabled) {
                emit('click')
            }
        }

        return {
            handleClick
        }
    }
}
</script>
