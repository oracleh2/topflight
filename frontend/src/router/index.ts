import {createRouter, createWebHistory} from 'vue-router'
import {useAuthStore} from '@/stores/auth'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            redirect: '/dashboard'
        },
        {
            path: '/login',
            name: 'Login',
            component: () => import('@/views/auth/Login.vue'),
            meta: {requiresGuest: true}
        },
        {
            path: '/register',
            name: 'Register',
            component: () => import('@/views/auth/Register.vue'),
            meta: {requiresGuest: true}
        },
        {
            path: '/dashboard',
            component: () => import('@/layouts/DashboardLayout.vue'),
            meta: {requiresAuth: true},
            children: [
                {
                    path: '',
                    name: 'Dashboard',
                    component: () => import('@/views/Dashboard.vue')
                },
                {
                    path: '/domains',
                    name: 'Domains',
                    component: () => import('@/views/domains/DomainsList.vue')
                },
                {
                    path: '/domains/:id/keywords',
                    name: 'DomainKeywords',
                    component: () => import('@/views/domains/DomainKeywords.vue'),
                    props: true
                },
                {
                    path: '/billing',
                    name: 'Billing',
                    component: () => import('@/views/billing/Billing.vue')
                },
                {
                    path: '/tasks',
                    name: 'Tasks',
                    component: () => import('@/views/tasks/TasksList.vue')
                },
                {
                    path: '/profile',
                    name: 'Profile',
                    component: () => import('@/views/profile/Profile.vue')
                },
                {
                    path: '/strategies',
                    name: 'Strategies',
                    component: () => import('@/views/strategies/StrategiesManager.vue')
                },
                {
                    path: "/admin/debug",
                    name: "TaskDebug",
                    component: () => import("@/components/admin/TaskDebugPanel.vue"),
                    meta: {requiresAuth: true, requiresAdmin: true}
                }
            ]
        }
    ]
})

router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // Проверяем требует ли маршрут авторизации
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next('/login')
        return
    }

    // Проверяем требует ли маршрут чтобы пользователь не был авторизован
    if (to.meta.requiresGuest && authStore.isAuthenticated) {
        next('/dashboard')
        return
    }

    // Загружаем профиль пользователя если он авторизован, но профиль не загружен
    if (authStore.isAuthenticated && !authStore.user) {
        try {
            await authStore.fetchProfile()
        } catch (error) {
            // Если не удалось загрузить профиль, разлогиниваем пользователя
            authStore.logout()
            next('/login')
            return
        }
    }

    // ← ДОБАВИТЬ ПРОВЕРКУ АДМИНСКИХ ПРАВ
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
        next('/dashboard')
        return
    }

    next()
})

export default router
