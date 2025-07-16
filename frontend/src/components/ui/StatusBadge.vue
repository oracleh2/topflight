<!-- frontend/src/components/ui/StatusBadge.vue -->

<template>
  <span
      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
      :class="getStatusClass(status)"
  >
    <svg
        class="w-2 h-2 mr-1.5"
        fill="currentColor"
        viewBox="0 0 8 8"
    >
      <circle cx="4" cy="4" r="3"/>
    </svg>
    {{ getStatusText(status) }}
  </span>
</template>

<script>
export default {
    name: 'StatusBadge',
    props: {
        status: {
            type: String,
            required: true,
            validator: (value) => ['critical', 'normal', 'max_reached'].includes(value)
        }
    },
    setup() {
        const getStatusText = (status) => {
            switch (status) {
                case 'critical':
                    return 'Критический'
                case 'normal':
                    return 'Нормальный'
                case 'max_reached':
                    return 'Максимум достигнут'
                default:
                    return 'Неизвестно'
            }
        }

        const getStatusClass = (status) => {
            switch (status) {
                case 'critical':
                    return 'bg-red-100 text-red-800'
                case 'normal':
                    return 'bg-green-100 text-green-800'
                case 'max_reached':
                    return 'bg-blue-100 text-blue-800'
                default:
                    return 'bg-gray-100 text-gray-800'
            }
        }

        return {
            getStatusText,
            getStatusClass
        }
    }
}
</script>
