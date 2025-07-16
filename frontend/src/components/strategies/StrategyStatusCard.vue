<!--frontend/src/components/strategies/StrategyStatusCard.vue-->

<template>
    <div class="bg-white rounded-lg shadow-md p-6 mb-4">
        <div class="flex justify-between items-start mb-4">
            <div>
                <h3 class="text-lg font-semibold text-gray-900">{{ strategy.name }}</h3>
                <p class="text-sm text-gray-600">{{ strategy.description }}</p>
            </div>
            <div class="flex items-center space-x-2">
                <StatusBadge :status="strategy.nurture_status?.status"/>
                <ActionButton
                    v-if="strategy.nurture_status?.needs_nurture"
                    @click="spawnTasks"
                    :loading="spawningTasks"
                />
            </div>
        </div>

        <!-- Информация о лимитах -->
        <div v-if="strategy.nurture_status" class="mt-4">
            <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium text-gray-700">Нагуленные профили:</span>
                <span class="text-sm text-gray-900">
          {{ strategy.nurture_status.current_count }} / {{ strategy.nurture_status.max_limit }}
        </span>
            </div>

            <!-- Прогресс-бар -->
            <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div
                    class="h-2 rounded-full transition-all duration-300"
                    :class="getProgressBarClass(strategy.nurture_status.status)"
                    :style="{ width: `${getProgressPercentage(strategy.nurture_status)}%` }"
                ></div>
            </div>

            <!-- Критическое предупреждение -->
            <div
                v-if="strategy.nurture_status.status === 'critical'"
                class="mt-3 p-3 bg-red-50 border border-red-200 rounded-md"
            >
                <div class="flex items-center">
                    <ExclamationTriangleIcon class="h-5 w-5 text-red-400 mr-2"/>
                    <div>
                        <p class="text-sm font-medium text-red-800">Критическое предупреждение!</p>
                        <p class="text-sm text-red-700">
                            Количество профилей ниже минимального лимита
                            ({{ strategy.nurture_status.min_limit }})
                        </p>
                    </div>
                </div>
            </div>

            <!-- Информация о лимитах -->
            <div class="mt-3 grid grid-cols-2 gap-4 text-sm">
                <div>
                    <span class="text-gray-600">Минимум:</span>
                    <span class="font-medium ml-1">{{ strategy.nurture_status.min_limit }}</span>
                </div>
                <div>
                    <span class="text-gray-600">Максимум:</span>
                    <span class="font-medium ml-1">{{ strategy.nurture_status.max_limit }}</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import {ref} from 'vue'
import {ExclamationTriangleIcon,} from '@heroicons/vue/24/outline'
import {useToast} from '@/composables/useToast'
import {strategiesApi} from '@/api/strategies'
import StatusBadge from "@/components/ui/StatusBadge.vue";
import ActionButton from "@/components/ui/ActionButton.vue";

export default {
    name: 'StrategyStatusCard',
    components: {
        ActionButton,
        StatusBadge,
        ExclamationTriangleIcon
    },
    props: {
        strategy: {
            type: Object,
            required: true
        }
    },
    emits: ['refresh'],
    setup(props, {emit}) {
        const toast = useToast()
        const spawningTasks = ref(false)

        const getProgressPercentage = (status) => {
            if (!status) return 0
            return Math.min((status.current_count / status.max_limit) * 100, 100)
        }

        const getProgressBarClass = (status) => {
            switch (status) {
                case 'critical':
                    return 'bg-red-500'
                case 'normal':
                    return 'bg-green-500'
                case 'max_reached':
                    return 'bg-blue-500'
                default:
                    return 'bg-gray-500'
            }
        }

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

        const spawnTasks = async () => {
            spawningTasks.value = true
            try {
                const response = await strategiesApi.spawnNurtureTasks(props.strategy.id)
                if (response.success) {
                    toast.success(`Создано ${response.tasks_created} задач нагула`)
                    emit('refresh')
                } else {
                    toast.error(response.message || 'Ошибка создания задач')
                }
            } catch (error) {
                toast.error('Ошибка создания задач нагула')
            } finally {
                spawningTasks.value = false
            }
        }

        return {
            spawningTasks,
            getProgressPercentage,
            getProgressBarClass,
            getStatusText,
            getStatusClass,
            spawnTasks
        }
    }
}
</script>

<style scoped>
/* Дополнительные стили при необходимости */
</style>
