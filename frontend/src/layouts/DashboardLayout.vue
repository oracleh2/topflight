<template>
    <div class="min-h-screen bg-gray-50 flex">
        <!-- Sidebar -->
        <div class="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0">
            <div
                class="flex flex-col flex-grow bg-white pt-5 pb-4 overflow-y-auto border-r border-gray-200">
                <div class="flex items-center flex-shrink-0 px-4">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div
                                class="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                                <span class="text-white font-bold text-sm">YP</span>
                            </div>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium text-gray-900">Yandex Parser</p>
                        </div>
                    </div>
                </div>

                <nav class="mt-8 flex-grow">
                    <div class="px-3 space-y-1">
                        <router-link
                            v-for="item in navigation"
                            :key="item.name"
                            :to="item.to"
                            :class="[
                $route.name === item.name
                  ? 'bg-primary-100 text-primary-900 border-r-2 border-primary-600'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors'
              ]"
                        >
                            <component
                                :is="item.icon"
                                :class="[
                  $route.name === item.name ? 'text-primary-600' : 'text-gray-400 group-hover:text-gray-500',
                  'mr-3 h-5 w-5'
                ]"
                                aria-hidden="true"
                            />
                            {{ item.label }}
                        </router-link>
                    </div>
                </nav>
            </div>
        </div>

        <!-- Main content -->
        <div class="lg:pl-64 flex flex-col flex-1">
            <!-- Top navigation -->
            <div
                class="relative z-10 flex-shrink-0 flex h-16 bg-white shadow border-b border-gray-200">
                <button
                    type="button"
                    class="px-4 border-r border-gray-200 text-gray-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 lg:hidden"
                    @click="sidebarOpen = true"
                >
                    <span class="sr-only">Open sidebar</span>
                    <Bars3Icon class="h-6 w-6" aria-hidden="true"/>
                </button>

                <div class="flex-1 px-4 flex justify-between sm:px-6 lg:px-8">
                    <div class="flex-1 flex items-center">
                        <h1 class="text-lg font-semibold text-gray-900">{{ pageTitle }}</h1>
                    </div>

                    <div class="ml-4 flex items-center md:ml-6">
                        <!-- Balance info -->
                        <div
                            class="hidden md:flex items-center mr-4 px-3 py-1 bg-gray-100 rounded-md">
                            <CurrencyDollarIcon class="h-4 w-4 text-gray-500 mr-1"/>
                            <span class="text-sm font-medium text-gray-700">
                {{
                                    formatCurrency(authStore.user?.current_balance || authStore.user?.balance || 0)
                                }}
              </span>
                        </div>

                        <!-- Profile dropdown -->
                        <Menu as="div" class="relative">
                            <div>
                                <MenuButton
                                    class="max-w-xs bg-white flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                                    <span class="sr-only">Open user menu</span>
                                    <div
                                        class="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center">
                                        <span class="text-xs font-medium text-white">{{
                                                userInitials
                                            }}</span>
                                    </div>
                                    <ChevronDownIcon class="ml-2 h-4 w-4 text-gray-400"/>
                                </MenuButton>
                            </div>

                            <transition
                                enter-active-class="transition ease-out duration-100"
                                enter-from-class="transform opacity-0 scale-95"
                                enter-to-class="transform opacity-100 scale-100"
                                leave-active-class="transition ease-in duration-75"
                                leave-from-class="transform opacity-100 scale-100"
                                leave-to-class="transform opacity-0 scale-95"
                            >
                                <MenuItems
                                    class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                                    <MenuItem v-slot="{ active }">
                                        <div class="px-4 py-3 border-b border-gray-100">
                                            <p class="text-sm text-gray-500">Вошли как</p>
                                            <p class="text-sm font-medium text-gray-900 truncate">
                                                {{ authStore.user?.email }}</p>
                                        </div>
                                    </MenuItem>

                                    <MenuItem v-slot="{ active }">
                                        <router-link
                                            to="/profile"
                                            :class="[active ? 'bg-gray-100' : '', 'block px-4 py-2 text-sm text-gray-700']"
                                        >
                                            Профиль
                                        </router-link>
                                    </MenuItem>

                                    <MenuItem v-slot="{ active }">
                                        <button
                                            @click="authStore.logout(); $router.push('/login')"
                                            :class="[active ? 'bg-gray-100' : '', 'block w-full text-left px-4 py-2 text-sm text-gray-700']"
                                        >
                                            Выйти
                                        </button>
                                    </MenuItem>
                                </MenuItems>
                            </transition>
                        </Menu>
                    </div>
                </div>
            </div>

            <!-- Page content with max width -->
            <main class="flex-1">
                <div class="py-6">
                    <!-- Ограничиваем ширину контента -->
                    <!--          <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">-->
                    <div class="py-6 px-4 sm:px-6 lg:px-8">

                        <router-view/>
                    </div>
                </div>
            </main>
        </div>

        <!-- Mobile sidebar -->
        <TransitionRoot as="template" :show="sidebarOpen">
            <Dialog as="div" class="relative z-40 lg:hidden" @close="sidebarOpen = false">
                <TransitionChild
                    as="template"
                    enter="transition-opacity ease-linear duration-300"
                    enter-from="opacity-0"
                    enter-to="opacity-100"
                    leave="transition-opacity ease-linear duration-300"
                    leave-from="opacity-100"
                    leave-to="opacity-0"
                >
                    <div class="fixed inset-0 bg-gray-600 bg-opacity-75"/>
                </TransitionChild>

                <div class="fixed inset-0 flex z-40">
                    <TransitionChild
                        as="template"
                        enter="transition ease-in-out duration-300 transform"
                        enter-from="-translate-x-full"
                        enter-to="translate-x-0"
                        leave="transition ease-in-out duration-300 transform"
                        leave-from="translate-x-0"
                        leave-to="-translate-x-full"
                    >
                        <DialogPanel
                            class="relative flex-1 flex flex-col max-w-xs w-full pt-5 pb-4 bg-white">
                            <TransitionChild
                                as="template"
                                enter="ease-in-out duration-300"
                                enter-from="opacity-0"
                                enter-to="opacity-100"
                                leave="ease-in-out duration-300"
                                leave-from="opacity-100"
                                leave-to="opacity-0"
                            >
                                <div class="absolute top-0 right-0 -mr-12 pt-2">
                                    <button
                                        type="button"
                                        class="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                                        @click="sidebarOpen = false"
                                    >
                                        <span class="sr-only">Close sidebar</span>
                                        <XMarkIcon class="h-6 w-6 text-white" aria-hidden="true"/>
                                    </button>
                                </div>
                            </TransitionChild>

                            <div class="flex-shrink-0 flex items-center px-4">
                                <div
                                    class="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                                    <span class="text-white font-bold text-sm">YP</span>
                                </div>
                                <span
                                    class="ml-3 text-sm font-medium text-gray-900">Yandex Parser</span>
                            </div>

                            <nav class="mt-8 flex-grow">
                                <div class="px-3 space-y-1">
                                    <router-link
                                        v-for="item in navigation"
                                        :key="item.name"
                                        :to="item.to"
                                        :class="[
                      $route.name === item.name
                        ? 'bg-primary-100 text-primary-900'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                      'group flex items-center px-3 py-2 text-sm font-medium rounded-md'
                    ]"
                                        @click="sidebarOpen = false"
                                    >
                                        <component
                                            :is="item.icon"
                                            :class="[
                        $route.name === item.name ? 'text-primary-600' : 'text-gray-400',
                        'mr-3 h-5 w-5'
                      ]"
                                        />
                                        {{ item.label }}
                                    </router-link>
                                </div>
                            </nav>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </Dialog>
        </TransitionRoot>
    </div>
</template>

<script setup lang="ts">
import {ref, computed} from 'vue'
import {useRoute} from 'vue-router'
import {
    Dialog,
    DialogPanel,
    Menu,
    MenuButton,
    MenuItem,
    MenuItems,
    TransitionChild,
    TransitionRoot,
} from '@headlessui/vue'
import {
    Bars3Icon,
    ChevronDownIcon,
    CurrencyDollarIcon,
    XMarkIcon,
    HomeIcon,
    GlobeAltIcon,
    CreditCardIcon,
    ClipboardDocumentListIcon,
    UserIcon
} from '@heroicons/vue/24/outline'
import {useAuthStore} from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const sidebarOpen = ref(false)

const navigation = [
    {name: 'Dashboard', label: 'Дашборд', to: '/dashboard', icon: HomeIcon},
    {name: 'Domains', label: 'Домены', to: '/domains', icon: GlobeAltIcon},
    {name: 'Billing', label: 'Биллинг', to: '/billing', icon: CreditCardIcon},
    {name: 'Tasks', label: 'Задачи', to: '/tasks', icon: ClipboardDocumentListIcon},
    {name: 'Profile', label: 'Профиль', to: '/profile', icon: UserIcon},
    {name: 'Strategies', label: 'Стратегии', to: '/strategies', icon: CurrencyDollarIcon},
]

const pageTitle = computed(() => {
    const current = navigation.find(item => item.name === route.name)
    return current?.label || 'Дашборд'
})

const userInitials = computed(() => {
    if (!authStore.user?.email) return 'U'
    return authStore.user.email.substring(0, 2).toUpperCase()
})

const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount)
}
</script>
