<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="sm:flex sm:items-center">
            <div class="sm:flex-auto">
                <h1 class="text-xl font-semibold text-gray-900">Домены</h1>
                <p class="mt-2 text-sm text-gray-700">
                    Управляйте доменами для отслеживания позиций в поисковой выдаче
                </p>
            </div>
            <div class="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
                <button
                    type="button"
                    class="btn-primary"
                    @click="showAddModal = true"
                >
                    Добавить домен
                </button>
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
            v-else-if="!domainsStore.domains.length"
            class="text-center py-12"
        >
            <GlobeAltIcon class="mx-auto h-12 w-12 text-gray-400"/>
            <h3 class="mt-2 text-sm font-medium text-gray-900">Нет доменов</h3>
            <p class="mt-1 text-sm text-gray-500">
                Добавьте первый домен для начала отслеживания позиций
            </p>
            <div class="mt-6">
                <button
                    type="button"
                    class="btn-primary"
                    @click="showAddModal = true"
                >
                    <PlusIcon class="-ml-1 mr-2 h-5 w-5" aria-hidden="true"/>
                    Добавить домен
                </button>
            </div>
        </div>

        <!-- Domains list -->
        <div v-else class="bg-white shadow sm:rounded-md overflow-visible">
            <ul role="list" class="divide-y divide-gray-200">
                <li
                    v-for="domain in domainsStore.domains"
                    :key="domain.id"
                    class="px-6 py-4 hover:bg-gray-50"
                >
                    <div class="flex items-center justify-between">
                        <div class="flex items-center min-w-0 flex-1">
                            <div class="flex-shrink-0">
                                <div
                                    :class="[
                    'h-10 w-10 rounded-lg flex items-center justify-center',
                    domain.is_verified ? 'bg-green-100' : 'bg-gray-100'
                  ]"
                                >
                                    <GlobeAltIcon
                                        :class="[
                      'h-6 w-6',
                      domain.is_verified ? 'text-green-600' : 'text-gray-400'
                    ]"
                                    />
                                </div>
                            </div>

                            <div class="ml-4 min-w-0 flex-1">
                                <div class="flex items-center">
                                    <router-link
                                        :to="`/domains/${domain.id}/keywords`"
                                        class="text-sm font-medium text-gray-900 truncate"
                                    >
                                        {{ domain.domain }}
                                    </router-link>
                                    <!--                                    <p class="text-sm font-medium text-gray-900 truncate">-->
                                    <!--                                        {{ domain.domain }}-->
                                    <!--                                    </p>-->
                                    <div
                                        v-if="domain.is_verified"
                                        class="ml-2 flex-shrink-0 flex"
                                    >
                                        <span
                                            class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                          <CheckIcon class="mr-1 h-3 w-3"/>
                                          Подтвержден
                                        </span>
                                    </div>
                                    <div
                                        v-else
                                        class="ml-2 flex-shrink-0 flex"
                                    >
                                      <span
                                          class="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                                      >
                                        <XCircleIcon class="mr-1 h-3 w-3"/>
                                        Не подтвержден
                                      </span>
                                    </div>

                                </div>

                                <div class="flex items-center mt-1 space-x-4">
                                    <p class="text-sm text-gray-500">
                                        {{ domain.keywords_count }} ключевых слов
                                    </p>
                                    <p v-if="domain.region" class="text-sm text-gray-500">
                                        Регион: {{ domain.region.name }} ({{ domain.region.code }})
                                    </p>
                                    <p class="text-sm text-gray-500">
                                        Добавлен {{ formatDate(domain.created_at) }}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div class="flex items-center space-x-2">
                            <router-link
                                :to="`/domains/${domain.id}/keywords`"
                                class="btn-secondary text-sm"
                            >
                                Ключевые слова
                            </router-link>

                            <Menu as="div" class="relative">
                                <MenuButton
                                    class="p-2 rounded-md text-gray-400 hover:text-gray-600">
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
                                        class="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                                        <MenuItem v-slot="{ active }">
                                            <button
                                                @click="editDomain(domain)"
                                                :class="[
                                            active ? 'bg-gray-100' : '',
                                            'block w-full text-left px-4 py-2 text-sm text-gray-700'
                                        ]"
                                            >
                                                <PencilIcon class="inline mr-2 h-4 w-4"/>
                                                Редактировать
                                            </button>
                                        </MenuItem>
                                        <MenuItem v-slot="{ active }">
                                            <button
                                                @click="confirmDelete(domain)"
                                                :class="[
                                            active ? 'bg-gray-100' : '',
                                            'block w-full text-left px-4 py-2 text-sm text-red-700'
                                        ]"
                                            >
                                                <TrashIcon class="inline mr-2 h-4 w-4"/>
                                                Удалить домен
                                            </button>
                                        </MenuItem>
                                    </MenuItems>
                                </transition>
                            </Menu>
                        </div>
                    </div>
                </li>
            </ul>
        </div>

        <!-- Add domain modal -->
        <AddDomainModal
            :isOpen="showAddModal"
            @close="showAddModal = false"
            @success="handleDomainAdded"
        />

        <!-- Edit domain modal -->
        <EditDomainModal
            :isOpen="showEditModal"
            :domain="domainToEdit"
            @close="showEditModal = false"
            @success="handleDomainEdited"
        />

        <!-- Delete confirmation modal -->
        <DeleteDomainModal
            :isOpen="showDeleteModal"
            :domain="domainToDelete"
            @close="showDeleteModal = false"
            @success="handleDomainDeleted"
        />
    </div>
</template>

<script setup lang="ts">
import {ref, onMounted} from 'vue'
import {Menu, MenuButton, MenuItem, MenuItems} from '@headlessui/vue'
import {
    GlobeAltIcon,
    PlusIcon,
    CheckIcon,
    EllipsisVerticalIcon,
    PencilIcon,
    TrashIcon,
    XCircleIcon
} from '@heroicons/vue/24/outline'
import {useDomainsStore, type Domain} from '@/stores/domains'
import Spinner from '@/components/ui/Spinner.vue'
import Alert from '@/components/ui/Alert.vue'
import AddDomainModal from '@/components/modals/AddDomainModal.vue'
import EditDomainModal from '@/components/modals/EditDomainModal.vue'
import DeleteDomainModal from '@/components/modals/DeleteDomainModal.vue'

const domainsStore = useDomainsStore()

const showAddModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const domainToEdit = ref<Domain | null>(null)
const domainToDelete = ref<Domain | null>(null)

const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    }).format(new Date(dateString))
}

const handleDomainAdded = () => {
    showAddModal.value = false
    // Обновляем список доменов
    domainsStore.fetchDomains()
}

const editDomain = (domain: Domain) => {
    domainToEdit.value = domain
    showEditModal.value = true
}

const handleDomainEdited = () => {
    showEditModal.value = false
    domainToEdit.value = null
    // Обновляем список доменов
    domainsStore.fetchDomains()
}

const confirmDelete = (domain: Domain) => {
    domainToDelete.value = domain
    showDeleteModal.value = true
}

const handleDomainDeleted = () => {
    showDeleteModal.value = false
    domainToDelete.value = null
    // Список доменов уже обновлен в store
}

onMounted(() => {
    domainsStore.fetchDomains()
})
</script>
