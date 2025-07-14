<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="sm:flex sm:items-center">
            <div class="sm:flex-auto">
                <nav class="flex mb-4" aria-label="Breadcrumb">
                    <ol role="list" class="flex items-center space-x-4">
                        <li>
                            <router-link to="/domains" class="text-gray-400 hover:text-gray-500">
                                <GlobeAltIcon class="flex-shrink-0 h-5 w-5" aria-hidden="true"/>
                                <span class="sr-only">Домены</span>
                            </router-link>
                        </li>
                        <li>
                            <div class="flex items-center">
                                <ChevronRightIcon class="flex-shrink-0 h-5 w-5 text-gray-400"
                                                  aria-hidden="true"/>
                                <span class="ml-4 text-sm font-medium text-gray-500">{{
                                        domainName
                                    }}</span>
                            </div>
                        </li>
                    </ol>
                </nav>

                <h1 class="text-xl font-semibold text-gray-900">
                    Ключевые слова для {{ domainName }}
                </h1>
                <p class="mt-2 text-sm text-gray-700">
                    Управляйте ключевыми словами для отслеживания позиций
                </p>
            </div>
            <div class="mt-4 sm:mt-0 sm:ml-16 sm:flex-none space-x-3">
                <button
                    type="button"
                    class="btn-secondary"
                    @click="showCheckPositionsModal = true"
                    :disabled="!selectedKeywords.length"
                >
                    Проверить позиции ({{ selectedKeywords.length }})
                </button>
                <button
                    type="button"
                    class="btn-secondary"
                    @click="showBulkModal = true"
                >
                    Массовое добавление
                </button>
                <button
                    type="button"
                    class="btn-primary"
                    @click="showAddModal = true"
                >
                    Добавить ключевое слово
                </button>

                <!--                <div class="mt-8">-->
                <!--                    <DomainProxySettings :domain-id="domainId"/>-->
                <!--                </div>-->
            </div>
        </div>

        <!-- Loading state -->
        <div v-if="domainsStore.loading" class="flex justify-center py-12">
            <Spinner class="h-8 w-8 text-primary-600"/>
        </div>

        <!-- Error state -->
        <Alert
            v-else-if="domainsStore.error"
            type="error"
            :message="domainsStore.error"
            dismissible
            @dismiss="domainsStore.error = null"
        />

        <!-- Empty state -->
        <div
            v-else-if="!domainsStore.selectedDomainKeywords.length"
            class="text-center py-12"
        >
            <MagnifyingGlassIcon class="mx-auto h-12 w-12 text-gray-400"/>
            <h3 class="mt-2 text-sm font-medium text-gray-900">Нет ключевых слов</h3>
            <p class="mt-1 text-sm text-gray-500">
                Добавьте первое ключевое слово для начала отслеживания позиций
            </p>
            <div class="mt-6">
                <button
                    type="button"
                    class="btn-primary"
                    @click="showAddModal = true"
                >
                    <PlusIcon class="-ml-1 mr-2 h-5 w-5" aria-hidden="true"/>
                    Добавить ключевое слово
                </button>
            </div>
        </div>

        <!-- Keywords table -->
        <div v-else class="bg-white shadow overflow-hidden sm:rounded-lg">
            <div class="px-4 py-3 border-b border-gray-200 sm:px-6">
                <div class="flex items-center justify-between">
                    <h3 class="text-lg leading-6 font-medium text-gray-900">
                        Ключевые слова ({{ domainsStore.selectedDomainKeywords.length }})
                    </h3>
                    <div class="flex items-center space-x-3">
                        <button
                            @click="selectAll"
                            class="text-sm text-primary-600 hover:text-primary-500"
                        >
                            {{ allSelected ? 'Снять выбор' : 'Выбрать все' }}
                        </button>
                    </div>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                    <tr>
                        <th scope="col"
                            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            <input
                                type="checkbox"
                                :checked="allSelected"
                                @change="selectAll"
                                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                            />
                        </th>
                        <th scope="col"
                            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Ключевое слово
                        </th>
                        <th scope="col"
                            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Регион
                        </th>
                        <th scope="col"
                            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Устройство
                        </th>
                        <th scope="col"
                            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Частота
                        </th>
                        <th scope="col"
                            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Статус
                        </th>
                        <th scope="col"
                            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Добавлено
                        </th>
                        <th scope="col" class="relative px-6 py-3">
                            <span class="sr-only">Действия</span>
                        </th>
                    </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                    <tr
                        v-for="keyword in domainsStore.selectedDomainKeywords"
                        :key="keyword.id"
                        :class="[
                selectedKeywords.includes(keyword.id) ? 'bg-primary-50' : 'hover:bg-gray-50'
              ]"
                    >
                        <td class="px-6 py-4 whitespace-nowrap">
                            <input
                                type="checkbox"
                                :value="keyword.id"
                                v-model="selectedKeywords"
                                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                            />
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm font-medium text-gray-900">
                                {{ keyword.keyword }}
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="text-sm text-gray-900">
                                {{ keyword.region.name }}
                            </div>
                            <div class="text-sm text-gray-500">
                                {{ keyword.region.code }}
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                <span
                    :class="[
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    keyword.device_type === 'desktop'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-green-100 text-green-800'
                  ]"
                >
                  <ComputerDesktopIcon
                      v-if="keyword.device_type === 'desktop'"
                      class="mr-1 h-3 w-3"
                  />
                  <DevicePhoneMobileIcon
                      v-else
                      class="mr-1 h-3 w-3"
                  />
                  {{ keyword.device_type === 'desktop' ? 'Десктоп' : 'Мобильный' }}
                </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {{ getFrequencyText(keyword.check_frequency) }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                <span
                    :class="[
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    keyword.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  ]"
                >
                  {{ keyword.is_active ? 'Активно' : 'Неактивно' }}
                </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {{ formatDate(keyword.created_at) }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <Menu as="div" class="relative inline-block text-left">
                                <MenuButton
                                    class="p-1 rounded-md text-gray-400 hover:text-gray-600">
                                    <EllipsisVerticalIcon class="h-5 w-5"/>
                                </MenuButton>

                                <transition
                                    enter-active-class="transition ease-out duration-100"
                                    enter-from-class="transform opacity-0 scale-95"
                                    enter-to-class="transform opacity-100 scale-100"
                                    leave-active-class="transition ease-in duration-75"
                                    leave-from-class="transform opacity-100 scale-100"
                                    leave-to-class="transform opacity-0 scale-95"
                                >
                                    <MenuItems
                                        class="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                                        <MenuItem v-slot="{ active }">
                                            <button
                                                @click="checkSinglePosition(keyword)"
                                                :class="[
                            active ? 'bg-gray-100' : '',
                            'block w-full text-left px-4 py-2 text-sm text-gray-700'
                          ]"
                                            >
                                                Проверить позицию
                                            </button>
                                        </MenuItem>
                                        <MenuItem v-slot="{ active }">
                                            <button
                                                @click="confirmDelete(keyword)"
                                                :class="[
                            active ? 'bg-gray-100' : '',
                            'block w-full text-left px-4 py-2 text-sm text-red-700'
                          ]"
                                            >
                                                Удалить
                                            </button>
                                        </MenuItem>
                                    </MenuItems>
                                </transition>
                            </Menu>
                        </td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="mt-8">
            <DomainProxySettings :domain-id="props.id"/>
        </div>

        <!-- Add keyword modal -->
        <AddKeywordModal
            :isOpen="showAddModal"
            :domainId="id"
            @close="showAddModal = false"
            @success="handleKeywordAdded"
        />

        <!-- Check positions modal -->
        <CheckPositionsModal
            :isOpen="showCheckPositionsModal"
            :keywordIds="selectedKeywords"
            @close="showCheckPositionsModal = false"
            @success="handlePositionsChecked"
        />

        <!-- Delete confirmation modal -->
        <Modal
            :isOpen="showDeleteModal"
            title="Удалить ключевое слово"
            @close="showDeleteModal = false"
        >
            <p class="text-sm text-gray-500">
                Вы уверены, что хотите удалить ключевое слово
                <strong>{{ keywordToDelete?.keyword }}</strong>?
                Это действие нельзя отменить.
            </p>

            <template #actions>
                <button
                    type="button"
                    class="btn-secondary"
                    @click="showDeleteModal = false"
                >
                    Отмена
                </button>
                <button
                    type="button"
                    class="btn-danger ml-3"
                    @click="deleteKeyword"
                    :disabled="domainsStore.loading"
                >
                    <Spinner v-if="domainsStore.loading" class="mr-2 h-4 w-4"/>
                    Удалить
                </button>
            </template>
        </Modal>
    </div>
    <!-- Bulk add keywords modal -->
    <BulkKeywordModal
        :isOpen="showBulkModal"
        :domainId="id"
        @close="showBulkModal = false"
        @success="handleBulkKeywordsAdded"
    />


</template>

<script setup lang="ts">
import {computed, onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {Menu, MenuButton, MenuItem, MenuItems} from '@headlessui/vue'
import {
    ChevronRightIcon,
    ComputerDesktopIcon,
    DevicePhoneMobileIcon,
    EllipsisVerticalIcon,
    GlobeAltIcon,
    MagnifyingGlassIcon,
    PlusIcon,
} from '@heroicons/vue/24/outline'
import {type Keyword, useDomainsStore} from '@/stores/domains'
import {useTasksStore} from '@/stores/tasks'
import Spinner from '@/components/ui/Spinner.vue'
import Alert from '@/components/ui/Alert.vue'
import Modal from '@/components/ui/Modal.vue'
import AddKeywordModal from '@/components/modals/AddKeywordModal.vue'
import CheckPositionsModal from '@/components/modals/CheckPositionsModal.vue'
import BulkKeywordModal from '@/components/modals/BulkKeywordModal.vue'
import DomainProxySettings from "@/components/domains/DomainProxySettings.vue";

interface Props {
    id: string
}

const props = defineProps<Props>()
const route = useRoute()
const router = useRouter()

const domainsStore = useDomainsStore()
const tasksStore = useTasksStore()

const showAddModal = ref(false)
const showBulkModal = ref(false)
const showCheckPositionsModal = ref(false)
const showDeleteModal = ref(false)
const keywordToDelete = ref<Keyword | null>(null)
const selectedKeywords = ref<string[]>([])

const domainName = computed(() => {
    const domain = domainsStore.domains.find(d => d.id === props.id)
    return domain?.domain || 'Неизвестный домен'
})

const allSelected = computed(() => {
    return selectedKeywords.value.length === domainsStore.selectedDomainKeywords.length &&
        domainsStore.selectedDomainKeywords.length > 0
})

const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    }).format(new Date(dateString))
}

const getFrequencyText = (frequency: string) => {
    const frequencyMap: Record<string, string> = {
        daily: 'Ежедневно',
        weekly: 'Еженедельно',
        monthly: 'Ежемесячно'
    }
    return frequencyMap[frequency] || frequency
}

const selectAll = () => {
    if (allSelected.value) {
        selectedKeywords.value = []
    } else {
        selectedKeywords.value = domainsStore.selectedDomainKeywords.map(k => k.id)
    }
}

const handleKeywordAdded = () => {
    showAddModal.value = false
    selectedKeywords.value = []
}

const handleBulkKeywordsAdded = (keywords: string[]) => {
    showBulkModal.value = false
    selectedKeywords.value = []
    // Показываем уведомление об успешном добавлении
    console.log(`Добавлено ${keywords.length} ключевых слов`)
}

const handlePositionsChecked = () => {
    showCheckPositionsModal.value = false
    selectedKeywords.value = []
    router.push('/tasks')
}

const checkSinglePosition = async (keyword: Keyword) => {
    selectedKeywords.value = [keyword.id]
    showCheckPositionsModal.value = true
}

const confirmDelete = (keyword: Keyword) => {
    keywordToDelete.value = keyword
    showDeleteModal.value = true
}

const deleteKeyword = async () => {
    if (!keywordToDelete.value) return

    try {
        await domainsStore.deleteKeyword(keywordToDelete.value.id, props.id)
        showDeleteModal.value = false
        keywordToDelete.value = null
        selectedKeywords.value = selectedKeywords.value.filter(id => id !== keywordToDelete.value?.id)
    } catch (error) {
        console.error('Error deleting keyword:', error)
    }
}

onMounted(async () => {
    // Загружаем домены если они не загружены
    if (!domainsStore.domains.length) {
        await domainsStore.fetchDomains()
    }

    // Загружаем ключевые слова домена
    await domainsStore.fetchDomainKeywords(props.id)
})
</script>
