import {defineStore} from 'pinia'
import {ref, computed} from 'vue'
import {api} from '@/api'

export interface User {
    id: string
    email: string
    subscription_plan: string
    balance: number
    current_balance: number
    reserved_balance: number
    api_key: string
    created_at: string
    domains_count: number
    keywords_count: number
    last_topup_amount?: number
    last_topup_date?: string
}

export const useAuthStore = defineStore('auth', () => {
    const user = ref<User | null>(null)
    const token = ref<string | null>(localStorage.getItem('access_token'))
    const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
    const loading = ref(false)
    const error = ref<string | null>(null)

    const isAuthenticated = computed(() => !!token.value)
    const availableBalance = computed(() =>
        user.value ? user.value.current_balance - user.value.reserved_balance : 0
    )

    async function login(email: string, password: string) {
        try {
            loading.value = true
            error.value = null

            const response = await api.login(email, password)
            const {access_token, refresh_token, user: userData} = response.data

            token.value = access_token
            refreshToken.value = refresh_token
            user.value = userData

            localStorage.setItem('access_token', access_token)
            localStorage.setItem('refresh_token', refresh_token)

            return true
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка авторизации'
            return false
        } finally {
            loading.value = false
        }
    }

    async function register(email: string, password: string) {
        try {
            loading.value = true
            error.value = null

            await api.register(email, password)
            return true
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка регистрации'
            return false
        } finally {
            loading.value = false
        }
    }

    async function refreshAccessToken() {
        if (!refreshToken.value) {
            throw new Error('No refresh token available')
        }

        try {
            const response = await api.refreshToken(refreshToken.value)

            if (response.status === 401) {
                logout()
            }

            const {access_token} = response.data

            token.value = access_token
            localStorage.setItem('access_token', access_token)
        } catch (err) {
            logout()
            throw err
        }
    }

    async function fetchProfile() {
        try {
            const response = await api.getProfile()
            user.value = response.data
        } catch (err: any) {
            if (err.response?.status === 401) {
                logout()
            }
            throw err
        }
    }

    async function changePassword(currentPassword: string, newPassword: string) {
        try {
            loading.value = true
            error.value = null

            await api.changePassword(currentPassword, newPassword)
            return true
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка изменения пароля'
            return false
        } finally {
            loading.value = false
        }
    }

    async function regenerateApiKey() {
        try {
            const response = await api.regenerateApiKey()
            if (user.value) {
                user.value.api_key = response.data.api_key
            }
            return response.data.api_key
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка генерации API ключа'
            throw err
        }
    }

    function logout() {
        user.value = null
        token.value = null
        refreshToken.value = null

        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')

        window.location.href = '/'
    }

    const isAdmin = computed(() => {
        if (!user.value?.email) return false

        // Проверка по email (как в бэкенде)
        const adminEmails = ['oracleh2@gmail.com']
        if (adminEmails.includes(user.value.email)) return true

        // Проверка по полю is_admin если есть
        if (user.value.is_admin) return true

        // Проверка по роли если есть
        if (user.value.role === 'admin') return true

        // Проверка по subscription_plan если есть
        if (user.value.subscription_plan === 'admin') return true

        return false
    })

    return {
        user,
        token,
        refreshToken,
        loading,
        error,
        isAuthenticated,
        availableBalance,
        isAdmin,

        login,
        register,
        refreshAccessToken,
        fetchProfile,
        changePassword,
        regenerateApiKey,
        logout,

    }
})
