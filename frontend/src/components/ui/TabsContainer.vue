<template>
    <div>
        <!-- Tab Navigation -->
        <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8">
                <button
                    v-for="tab in tabs"
                    :key="tab.id"
                    @click="$emit('change', tab.id)"
                    :class="[
                        activeTab === tab.id
                            ? 'border-primary-500 text-primary-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                        'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center'
                    ]"
                >
                    <component
                        :is="tab.icon"
                        class="h-4 w-4 mr-2"
                        :class="activeTab === tab.id ? 'text-primary-500' : 'text-gray-400'"
                    />
                    {{ tab.label }}
                    <span
                        v-if="tab.hasError"
                        class="ml-1 h-2 w-2 bg-red-500 rounded-full"
                    ></span>
                </button>
            </nav>
        </div>

        <!-- Tab Content -->
        <div class="mt-6">
            <slot></slot>
        </div>
    </div>
</template>

<script setup lang="ts">
interface Tab {
    id: string
    label: string
    icon: any
    hasError?: boolean
}

interface Props {
    tabs: Tab[]
    activeTab: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
    change: [tabId: string]
}>()
</script>
