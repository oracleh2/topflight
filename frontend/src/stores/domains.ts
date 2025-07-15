import {defineStore} from 'pinia'
import {ref} from 'vue'
import {api} from '@/api'

export interface Region {
    id: string
    code: string
    name: string
    country_code: string
    region_type?: string
}

export interface Domain {
    id: string
    domain: string
    is_verified: boolean
    created_at: string
    keywords_count: number
    region?: Region // Добавляем регион к домену
}

export interface Keyword {
    id: string
    keyword: string
    region: Region
    device_type: string
    is_active: boolean
    check_frequency: string
    created_at: string
}

export const useDomainsStore = defineStore('domains', () => {
    const domains = ref<Domain[]>([])
    const regions = ref<Region[]>([])
    const selectedDomainKeywords = ref<Keyword[]>([])
    const loading = ref(false)
    const error = ref<string | null>(null)

    /**
     * Поиск регионов по названию или коду
     * @param query - строка поиска (название или код региона)
     * @param limit - максимальное количество результатов (по умолчанию 20)
     */
    async function searchRegions(query: string, limit = 20): Promise<Region[]> {
        if (query.length < 2) {
            return []
        }

        try {
            const response = await api.searchRegions(query, limit)
            return response.data
        } catch (error) {
            console.error('Error searching regions:', error)
            this.error = 'Ошибка поиска регионов'
            return []
        }
    }

    /**
     * Загрузка всех регионов (для обратной совместимости)
     */
    async function fetchRegions() {
        if (this.regions.length > 0) {
            return // Регионы уже загружены
        }

        this.loading = true
        this.error = null

        try {
            const response = await api.getRegions()
            this.regions = response.data
        } catch (error) {
            console.error('Error fetching regions:', error)
            this.error = 'Ошибка загрузки регионов'
        } finally {
            this.loading = false
        }
    }

    async function fetchDomains() {
        try {
            loading.value = true
            const response = await api.getDomains()
            domains.value = response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка загрузки доменов'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function addDomain(domain: string, regionId: string) {
        try {
            loading.value = true
            error.value = null

            const response = await api.addDomain(domain, regionId)
            await fetchDomains() // Обновляем список доменов
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка добавления домена'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function updateDomain(domainId: string, data: {
        domain: string
        region_id: string
        is_verified: boolean
    }) {
        try {
            loading.value = true
            error.value = null

            const response = await api.updateDomain(domainId, data)
            await fetchDomains() // Обновляем список доменов
            return response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка обновления домена'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function deleteDomain(domainId: string) {
        try {
            loading.value = true
            await api.deleteDomain(domainId)

            // Удаляем домен из локального состояния
            domains.value = domains.value.filter(d => d.id !== domainId)
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка удаления домена'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function fetchDomainKeywords(domainId: string) {
        try {
            loading.value = true
            const response = await api.getDomainKeywords(domainId)
            selectedDomainKeywords.value = response.data
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка загрузки ключевых слов'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function addKeyword(
        domainId: string,
        keyword: string,
        regionId: string,
        deviceType: string,
        checkFrequency: string = 'daily',
        isActive: boolean = true
    ) {
        try {
            loading.value = true
            error.value = null

            await api.addKeyword(domainId, keyword, regionId, deviceType, checkFrequency, isActive)
            await fetchDomainKeywords(domainId) // Обновляем список ключевых слов
            await fetchDomains() // Обновляем счетчики
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка добавления ключевого слова'
            throw err
        } finally {
            loading.value = false
        }
    }

    async function deleteKeyword(keywordId: string, domainId: string) {
        try {
            loading.value = true
            await api.deleteKeyword(keywordId)

            // Удаляем ключевое слово из локального состояния
            selectedDomainKeywords.value = selectedDomainKeywords.value.filter(k => k.id !== keywordId)
            await fetchDomains() // Обновляем счетчики
        } catch (err: any) {
            error.value = err.response?.data?.detail || 'Ошибка удаления ключевого слова'
            throw err
        } finally {
            loading.value = false
        }
    }

    /**
     * Массовое удаление ключевых слов
     */
    async function bulkDeleteKeywords(keywordIds: string[]) {
        this.loading = true
        this.error = null

        try {
            const response = await api.bulkDeleteKeywords(keywordIds)
            return response.data
        } catch (error) {
            console.error('Error bulk deleting keywords:', error)
            this.error = 'Ошибка массового удаления ключевых слов'
            throw error
        } finally {
            this.loading = false
        }
    }

    return {
        domains,
        regions,
        selectedDomainKeywords,
        loading,
        error,
        searchRegions,
        fetchDomains,
        fetchRegions,
        addDomain,
        updateDomain,
        deleteDomain,
        fetchDomainKeywords,
        addKeyword,
        deleteKeyword,
        bulkDeleteKeywords
    }
})
