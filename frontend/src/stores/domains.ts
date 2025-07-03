import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'

export interface Region {
  id: string
  code: string
  name: string
  country_code: string
}

export interface Domain {
  id: string
  domain: string
  is_verified: boolean
  created_at: string
  keywords_count: number
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

  async function fetchRegions() {
    try {
      const response = await api.getRegions()
      regions.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки регионов'
      throw err
    }
  }

  async function addDomain(domain: string) {
    try {
      loading.value = true
      error.value = null

      const response = await api.addDomain(domain)
      await fetchDomains() // Обновляем список доменов
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка добавления домена'
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

  async function addKeyword(domainId: string, keyword: string, regionId: string, deviceType: string) {
    try {
      loading.value = true
      error.value = null

      await api.addKeyword(domainId, keyword, regionId, deviceType)
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

  return {
    domains,
    regions,
    selectedDomainKeywords,
    loading,
    error,
    fetchDomains,
    fetchRegions,
    addDomain,
    deleteDomain,
    fetchDomainKeywords,
    addKeyword,
    deleteKeyword
  }
})
