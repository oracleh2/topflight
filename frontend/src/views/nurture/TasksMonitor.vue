<!-- frontend/src/views/nurture/TasksMonitor.vue -->
<template>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
            <h1 class="text-2xl font-bold text-gray-900 mb-6">
                Мониторинг задач нагула профилей
            </h1>

            <!-- Фильтры по стратегиям -->
            <div class="mb-6">
                <select
                    v-model="selectedStrategyId"
                    @change="refreshTasks"
                    class="block w-64 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
                    <option value="">Все стратегии</option>
                    <option
                        v-for="strategy in strategies"
                        :key="strategy.id"
                        :value="strategy.id"
                    >
                        {{ strategy.name }}
                    </option>
                </select>
            </div>

            <!-- Компонент мониторинга -->
            <ProfileNurtureTasksMonitor
                v-if="selectedStrategyId"
                :strategy-id="selectedStrategyId"
            />

            <div v-else class="text-center py-12 text-gray-500">
                Выберите стратегию для просмотра задач
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, onMounted, computed} from 'vue'
import {useStrategiesStore} from '@/stores/strategies'
import ProfileNurtureTasksMonitor from '@/components/strategies/ProfileNurtureTasksMonitor.vue'

const strategiesStore = useStrategiesStore()
const selectedStrategyId = ref('')

const strategies = computed(() => strategiesStore.profileNurtureStrategies)

const refreshTasks = () => {
    console.log('TasksMonitor refreshTasks called for strategy:', selectedStrategyId.value)
    // Эмитим событие для обновления монитора
    // Или можно перезагрузить компонент принудительно
}

onMounted(() => {
    strategiesStore.fetchStrategies('profile_nurture')
    if (strategies.value.length > 0) {
        selectedStrategyId.value = strategies.value[0].id
    }
})
</script>

