<template>
    <div class="space-y-6">
        <!-- Статистика прокси -->
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div class="bg-gray-50 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <ChartBarIcon class="h-5 w-5 text-gray-400"/>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">Всего прокси</p>
                        <p class="text-lg font-semibold text-gray-900">{{ stats.total_proxies }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-green-50 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <CheckCircleIcon class="h-5 w-5 text-green-400"/>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">Активных</p>
                        <p class="text-lg font-semibold text-green-600">{{
                                stats.active_proxies
                            }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-red-50 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <XCircleIcon class="h-5 w-5 text-red-400"/>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">Неактивных</p>
                        <p class="text-lg font-semibold text-red-600">{{ stats.failed_proxies }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-blue-50 rounded-lg p-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <CpuChipIcon class="h-5 w-5 text-blue-400"/>
                    </div>
                    <div class="ml-3 flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">Успешность</p>
                        <p class="text-lg font-semibold text-blue-600">
                            {{ stats.success_rate ? Math.round(stats.success_rate) + '%' : 'Н/Д' }}
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Добавление прокси -->
        <div class="border rounded-lg p-4">
            <h4 class="text-md font-medium text-gray-900 mb-4">Добавить прокси</h4>

            <!-- Выбор типа импорта -->
            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Способ импорта
                </label>
                <div class="grid grid-cols-2 gap-3 sm:grid-cols-5">
                    <button
                        v-for="type in importTypes"
                        :key="type.value"
                        type="button"
                        @click="selectedImportType = type.value"
                        :class="[
                            'p-3 border-2 rounded-lg text-left transition-colors',
                            selectedImportType === type.value
                                ? 'border-primary-500 bg-primary-50'
                                : 'border-gray-200 hover:border-gray-300'
                        ]"
                    >
                        <div class="flex flex-col items-center">
                            <component :is="type.icon" class="h-5 w-5 mb-1"/>
                            <span class="text-xs font-medium">{{ type.label }}</span>
                        </div>
                    </button>
                </div>
            </div>

            <!-- Форма ввода в зависимости от типа -->
            <div class="mb-4">
                <div v-if="selectedImportType === 'manual_list'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Прокси (построчно)
                    </label>
                    <textarea
                        v-model="manualProxyText"
                        rows="6"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="192.168.1.1:8080:username:password
192.168.1.2:3128
socks5://192.168.1.3:1080:user:pass"
                    ></textarea>
                    <p class="text-xs text-gray-500 mt-1">
                        Поддерживаемые форматы: host:port, host:port:user:pass,
                        protocol://host:port:user:pass
                    </p>
                </div>

                <div v-if="selectedImportType === 'file_upload'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Выберите файл
                    </label>
                    <input
                        ref="fileInput"
                        type="file"
                        accept=".txt,.csv"
                        @change="handleFileSelect"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                    <p class="text-xs text-gray-500 mt-1">
                        Поддерживаемые форматы: .txt, .csv
                    </p>
                </div>

                <div v-if="selectedImportType === 'url_import'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        URL для импорта
                    </label>
                    <input
                        v-model="importUrl"
                        type="url"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="https://example.com/proxies.txt"
                    >
                    <p class="text-xs text-gray-500 mt-1">
                        URL должен возвращать список прокси в текстовом формате
                    </p>
                </div>

                <div v-if="selectedImportType === 'google_docs'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Ссылка на Google Документ
                    </label>
                    <input
                        v-model="googleDocUrl"
                        type="url"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="https://docs.google.com/document/d/..."
                    >
                    <p class="text-xs text-gray-500 mt-1">
                        Документ должен быть доступен для чтения по ссылке
                    </p>
                </div>

                <div v-if="selectedImportType === 'google_sheets'">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Ссылка на Google Таблицы
                    </label>
                    <input
                        v-model="googleSheetsUrl"
                        type="url"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="https://docs.google.com/spreadsheets/d/..."
                    >
                    <p class="text-xs text-gray-500 mt-1">
                        Таблица должна быть доступна для чтения по ссылке
                    </p>
                </div>
            </div>

            <!-- Кнопка импорта -->
            <div class="flex justify-end">
                <button
                    type="button"
                    @click="importProxies"
                    :disabled="loading || !canImport"
                    class="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-400"
                >
                    <span v-if="loading">
                        <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline"
                             xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                    stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor"
                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Импорт...
                    </span>
                    <span v-else>
                        Импортировать прокси
                    </span>
                </button>
            </div>

            <!-- Результат импорта -->
            <div v-if="importResult" class="mt-4 p-4 rounded-lg" :class="[
                importResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            ]">
                <div class="flex items-center">
                    <CheckCircleIcon v-if="importResult.success"
                                     class="h-5 w-5 text-green-500 mr-2"/>
                    <XCircleIcon v-else class="h-5 w-5 text-red-500 mr-2"/>
                    <p class="text-sm font-medium" :class="[
                        importResult.success ? 'text-green-800' : 'text-red-800'
                    ]">
                        {{ importResult.success ? 'Импорт завершен успешно' : 'Ошибка импорта' }}
                    </p>
                </div>
                <div v-if="importResult.success" class="mt-2 text-sm text-green-700">
                    <p>{{ importResult.message || 'Импорт завершен успешно' }}</p>
                    <p v-if="importResult.successfully_imported > 0">
                        Статически импортировано: {{ importResult.successfully_imported }}
                    </p>
                    <p>Всего найдено: {{ importResult.total_parsed }}</p>
                    <p v-if="importResult.failed_imports > 0">
                        Ошибок: {{ importResult.failed_imports }}
                    </p>
                </div>
                <div v-if="importResult.errors && importResult.errors.length > 0" class="mt-2">
                    <p class="text-sm font-medium text-red-800">Ошибки:</p>
                    <ul class="mt-1 text-sm text-red-700">
                        <li v-for="error in importResult.errors" :key="error">{{ error }}</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Настройки прокси -->
        <div class="border rounded-lg p-4">
            <h4 class="text-md font-medium text-gray-900 mb-4">Настройки прокси</h4>
            <div class="space-y-4">
                <div class="flex items-center justify-between">
                    <div>
                        <label class="text-sm font-medium text-gray-700">Использовать прокси</label>
                        <p class="text-sm text-gray-500">Включить использование прокси для этой
                            стратегии</p>
                    </div>
                    <input
                        v-model="proxySettings.use_proxy"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        @change="updateProxySettings"
                    >
                </div>

                <div class="flex items-center justify-between">
                    <div>
                        <label class="text-sm font-medium text-gray-700">Ротация прокси</label>
                        <p class="text-sm text-gray-500">Автоматически менять прокси после
                            определенного количества запросов</p>
                    </div>
                    <input
                        v-model="proxySettings.proxy_rotation"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        @change="updateProxySettings"
                    >
                </div>

                <div v-if="proxySettings.proxy_rotation" class="flex items-center justify-between">
                    <div>
                        <label class="text-sm font-medium text-gray-700">Интервал ротации</label>
                        <p class="text-sm text-gray-500">Количество запросов до смены прокси</p>
                    </div>
                    <input
                        v-model.number="proxySettings.proxy_rotation_interval"
                        type="number"
                        min="1"
                        max="100"
                        class="w-20 px-2 py-1 border border-gray-300 rounded-md text-sm"
                        @blur="updateProxySettings"
                    >
                </div>

                <div class="flex items-center justify-between">
                    <div>
                        <label class="text-sm font-medium text-gray-700">Запасные прокси</label>
                        <p class="text-sm text-gray-500">Использовать другие прокси при сбое
                            основной</p>
                    </div>
                    <input
                        v-model="proxySettings.fallback_on_error"
                        type="checkbox"
                        class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        @change="updateProxySettings"
                    >
                </div>
            </div>
        </div>

        <!-- Список прокси -->
        <div class="border rounded-lg">
            <div class="px-4 py-3 border-b border-gray-200">
                <div class="flex items-center justify-between">
                    <h4 class="text-md font-medium text-gray-900">Список прокси</h4>
                    <div class="flex items-center space-x-2">
                        <!-- Переключатель отображения -->
                        <div class="flex items-center space-x-2">
                            <button
                                type="button"
                                @click="showMode = 'static'"
                                :class="[
                            'px-3 py-1 text-xs font-medium rounded-md transition-colors',
                            showMode === 'static'
                                ? 'bg-gray-900 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        ]"
                            >
                                Статические
                            </button>
                            <button
                                type="button"
                                @click="showMode = 'dynamic'"
                                :class="[
                            'px-3 py-1 text-xs font-medium rounded-md transition-colors',
                            showMode === 'dynamic'
                                ? 'bg-blue-600 text-white'
                                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                        ]"
                            >
                                Динамические
                            </button>
                        </div>

                        <!-- Кнопка обновления для динамических -->
                        <button
                            v-if="showMode === 'dynamic'"
                            type="button"
                            @click="refreshDynamicProxies"
                            :disabled="loadingDynamic"
                            class="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 disabled:opacity-50"
                        >
                            <ArrowPathIcon
                                :class="['h-3 w-3 mr-1', loadingDynamic ? 'animate-spin' : '']"
                            />
                            Обновить
                        </button>
                    </div>
                </div>
            </div>

            <!-- Статические прокси -->
            <div v-if="showMode === 'static'" class="divide-y divide-gray-200">
                <div
                    v-for="proxy in proxies"
                    :key="proxy.id"
                    class="p-4 hover:bg-gray-50"
                >
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <div
                                :class="[
                            'h-2 w-2 rounded-full',
                            proxy.status === 'active' ? 'bg-green-500' : 'bg-red-500'
                        ]"
                            ></div>
                            <div>
                                <p class="text-sm font-medium text-gray-900">
                                    {{ proxy.host }}:{{ proxy.port }}
                                </p>
                                <div class="flex items-center space-x-2 text-xs text-gray-500">
                                    <span>{{ proxy.protocol.toUpperCase() }}</span>
                                    <span>•</span>
                                    <span>Использований: {{ proxy.total_uses }}</span>
                                    <span>•</span>
                                    <span>Успешность: {{ proxy.success_rate }}%</span>
                                    <span>•</span>
                                    <span class="inline-flex items-center">
                                <ArchiveBoxIcon class="h-3 w-3 mr-1"/>
                                Статическая
                            </span>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                    <span :class="[
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        proxy.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    ]">
                        {{ proxy.status === 'active' ? 'Активна' : 'Неактивна' }}
                    </span>
                            <button
                                type="button"
                                @click="testProxy(proxy)"
                                class="text-blue-600 hover:text-blue-900 text-sm font-medium"
                            >
                                Тест
                            </button>
                        </div>
                    </div>
                </div>

                <div v-if="proxies.length === 0" class="p-4 text-center text-gray-500">
                    <ArchiveBoxIcon class="h-8 w-8 mx-auto mb-2 text-gray-400"/>
                    <p>Статические прокси не добавлены</p>
                    <p class="text-sm mt-1">Импортируйте прокси через "Ручной ввод" или "Файл"</p>
                </div>
            </div>

            <!-- Динамические прокси -->
            <div v-else-if="showMode === 'dynamic'" class="divide-y divide-gray-200">
                <!-- Информационный блок -->
                <div class="p-4 bg-blue-50 border-b border-blue-200">
                    <div class="flex items-center">
                        <ArrowPathIcon class="h-5 w-5 text-blue-600 mr-2"/>
                        <div>
                            <p class="text-sm font-medium text-blue-900">Динамические прокси</p>
                            <p class="text-xs text-blue-700 mt-1">
                                Прокси загружаются в реальном времени из внешних источников при
                                каждом использовании профиля
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Источники с превью прокси -->
                <div
                    v-for="source in dynamicSources"
                    :key="source.id"
                    class="p-4 hover:bg-gray-50"
                >
                    <div class="mb-3">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center">
                                <component :is="getSourceIcon(source.source_type)"
                                           class="h-4 w-4 text-blue-600 mr-2"/>
                                <span class="text-sm font-medium text-gray-900">
                            {{ getSourceTypeLabel(source.source_type) }}
                        </span>
                                <span
                                    class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {{ source.proxy_count }} прокси
                        </span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <button
                                    type="button"
                                    @click="refreshSourcePreview(source.id)"
                                    :disabled="refreshingPreview === source.id"
                                    class="text-blue-600 hover:text-blue-900 text-sm font-medium disabled:opacity-50"
                                >
                                    <ArrowPathIcon
                                        :class="['h-4 w-4', refreshingPreview === source.id ? 'animate-spin' : '']"
                                    />
                                </button>
                                <button
                                    type="button"
                                    @click="toggleSourcePreview(source.id)"
                                    class="text-gray-600 hover:text-gray-900 text-sm font-medium"
                                >
                                    {{
                                        expandedSources.includes(source.id) ? 'Скрыть' : 'Показать'
                                    }}
                                </button>
                            </div>
                        </div>

                        <p class="text-xs text-gray-500 mt-1">
                            {{ truncateUrl(source.source_url) }}
                        </p>
                    </div>

                    <!-- Превью прокси из источника -->
                    <div v-if="expandedSources.includes(source.id)" class="mt-3">
                        <div
                            v-if="sourcePreviewData[source.id] && sourcePreviewData[source.id].length > 0"
                            class="space-y-2">
                            <div class="text-xs text-gray-500 mb-2">
                                Превью (последние
                                {{ Math.min(5, sourcePreviewData[source.id].length) }} из
                                {{ sourcePreviewData[source.id].length }}):
                            </div>
                            <div
                                v-for="(proxy, index) in sourcePreviewData[source.id].slice(0, 5)"
                                :key="index"
                                class="flex items-center pl-4 py-2 bg-gray-50 rounded"
                            >
                                <div class="h-2 w-2 rounded-full bg-blue-500 mr-3"></div>
                                <div>
                                    <p class="text-sm font-medium text-gray-900">
                                        {{ proxy.host }}:{{ proxy.port }}
                                    </p>
                                    <div class="flex items-center space-x-2 text-xs text-gray-500">
                                        <span>{{ proxy.protocol.toUpperCase() }}</span>
                                        <span>•</span>
                                        <span class="inline-flex items-center">
                        <ArrowPathIcon class="h-3 w-3 mr-1"/>
                        Загружается динамически
                    </span>
                                    </div>
                                </div>
                            </div>

                            <div v-if="sourcePreviewData[source.id].length > 5"
                                 class="text-xs text-gray-500 text-center py-2">
                                ... и еще {{ sourcePreviewData[source.id].length - 5 }} прокси
                            </div>
                        </div>

                        <!-- Состояние ошибки -->
                        <div
                            v-else-if="sourcePreviewData[source.id] && sourcePreviewData[source.id].length === 0"
                            class="text-center py-4">
                            <ExclamationTriangleIcon class="h-5 w-5 mx-auto text-amber-500 mb-2"/>
                            <p class="text-sm text-amber-700">Не удалось загрузить прокси из
                                источника</p>
                            <button
                                type="button"
                                @click="refreshSourcePreview(source.id)"
                                class="text-blue-600 hover:text-blue-900 text-sm font-medium mt-2"
                            >
                                Попробовать снова
                            </button>
                        </div>

                        <div v-else-if="refreshingPreview === source.id" class="text-center py-4">
                            <ArrowPathIcon class="h-5 w-5 animate-spin mx-auto text-blue-600"/>
                            <p class="text-sm text-gray-500 mt-2">Загрузка прокси...</p>
                        </div>

                        <div v-else class="text-center py-4">
                            <button
                                type="button"
                                @click="refreshSourcePreview(source.id)"
                                class="text-blue-600 hover:text-blue-900 text-sm font-medium"
                            >
                                Загрузить превью
                            </button>
                        </div>
                    </div>
                </div>

                <div v-if="dynamicSources.length === 0" class="p-4 text-center text-gray-500">
                    <ArrowPathIcon class="h-8 w-8 mx-auto mb-2 text-gray-400"/>
                    <p>Динамические источники не добавлены</p>
                    <p class="text-sm mt-1">Импортируйте прокси через "URL", "Google Docs" или
                        "Google Sheets"</p>
                </div>
            </div>
        </div>

        <!-- Источники прокси -->
        <div v-if="proxySources.length > 0" class="border rounded-lg mt-6">
            <div class="px-4 py-3 border-b border-gray-200">
                <h4 class="text-md font-medium text-gray-900">Источники прокси</h4>
            </div>
            <div class="divide-y divide-gray-200">
                <div
                    v-for="source in proxySources"
                    :key="source.id"
                    class="p-4 hover:bg-gray-50"
                >
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="flex items-center">
                                <p class="text-sm font-medium text-gray-900">
                                    {{ getSourceTypeLabel(source.source_type) }}
                                </p>
                                <!-- Индикатор динамического источника -->
                                <span
                                    v-if="isDynamicSource(source.source_type)"
                                    class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                                >
                            <ArrowPathIcon class="h-3 w-3 mr-1"/>
                            Динамический
                        </span>
                                <span
                                    v-else
                                    class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                                >
                            <ArchiveBoxIcon class="h-3 w-3 mr-1"/>
                            Статический
                        </span>
                            </div>
                            <div class="mt-1 text-xs text-gray-500">
                                <p>{{ formatDate(source.created_at) }} • {{ source.proxy_count }}
                                    прокси</p>
                                <!-- Описание для динамических источников -->
                                <p v-if="isDynamicSource(source.source_type)"
                                   class="mt-1 text-blue-600">
                                    <InformationCircleIcon class="h-3 w-3 inline mr-1"/>
                                    Прокси загружаются динамически при каждом использовании
                                </p>
                                <p v-else class="mt-1 text-gray-600">
                                    <InformationCircleIcon class="h-3 w-3 inline mr-1"/>
                                    Прокси импортированы в базу данных
                                </p>
                            </div>
                            <!-- URL для динамических источников -->
                            <div v-if="isDynamicSource(source.source_type) && source.source_url"
                                 class="mt-2">
                                <p class="text-xs text-gray-500">
                                    <LinkIcon class="h-3 w-3 inline mr-1"/>
                                    {{ truncateUrl(source.source_url) }}
                                </p>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <!-- Кнопка обновления для динамических источников -->
                            <button
                                v-if="isDynamicSource(source.source_type)"
                                type="button"
                                @click="refreshDynamicSource(source.id)"
                                :disabled="refreshingSource === source.id"
                                class="text-blue-600 hover:text-blue-900 text-sm font-medium disabled:opacity-50"
                            >
                                <ArrowPathIcon
                                    :class="['h-4 w-4', refreshingSource === source.id ? 'animate-spin' : '']"
                                />
                            </button>
                            <button
                                type="button"
                                @click="deleteProxySource(source.id)"
                                class="text-red-600 hover:text-red-900 text-sm font-medium"
                            >
                                Удалить
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, watch} from 'vue'
import {
    ArrowPathIcon,
    ExclamationTriangleIcon,
    InformationCircleIcon,
    ArchiveBoxIcon,
    ChartBarIcon,
    CheckCircleIcon,
    XCircleIcon,
    CpuChipIcon,
    DocumentTextIcon,
    ArrowUpTrayIcon,
    LinkIcon,
    DocumentIcon,
    TableCellsIcon
} from '@heroicons/vue/24/outline'
import {useStrategiesStore} from '@/stores/strategies'
import {api} from '@/api'

interface ProxyItem {
    id: string
    host: string
    port: number
    protocol: string
    status: string
    total_uses: number
    success_rate: number
}

interface ProxySource {
    id: string
    source_type: string
    created_at: string
    proxy_count: number
    source_url: string
}

// Props
interface Props {
    strategyId: string
}

const props = defineProps<Props>()

// Store
const strategiesStore = useStrategiesStore()

// Reactive data
const loading = ref(false)
const proxies = ref<ProxyItem[]>([])
const proxySources = ref<ProxySource[]>([])
const refreshingSource = ref<string | null>(null)
const stats = ref({
    total_proxies: 0,
    active_proxies: 0,
    failed_proxies: 0,
    success_rate: null
})
const proxySettings = ref({
    use_proxy: true,
    proxy_rotation: true,
    proxy_rotation_interval: 10,
    fallback_on_error: true,
    max_retries: 3,
    retry_delay: 5
})

// Import data
const selectedImportType = ref('manual_list')
const manualProxyText = ref('')
const importUrl = ref('')
const googleDocUrl = ref('')
const googleSheetsUrl = ref('')
const selectedFile = ref<File | null>(null)
const importResult = ref<any>(null)
const showMode = ref<'static' | 'dynamic'>('static')
const loadingDynamic = ref(false)
const refreshingPreview = ref<string | null>(null)
const expandedSources = ref<string[]>([])
const sourcePreviewData = ref<Record<string, any[]>>({})

// Computed
const importTypes = computed(() => [
    {
        value: 'manual_list',
        label: 'Ручной ввод',
        icon: DocumentTextIcon
    },
    {
        value: 'file_upload',
        label: 'Файл',
        icon: ArrowUpTrayIcon
    },
    {
        value: 'url_import',
        label: 'URL',
        icon: LinkIcon
    },
    {
        value: 'google_docs',
        label: 'Google Docs',
        icon: DocumentIcon
    },
    {
        value: 'google_sheets',
        label: 'Google Sheets',
        icon: TableCellsIcon
    }
])

const canImport = computed(() => {
    switch (selectedImportType.value) {
        case 'manual_list':
            return manualProxyText.value.trim().length > 0
        case 'file_upload':
            return selectedFile.value !== null
        case 'url_import':
            return importUrl.value.trim().length > 0
        case 'google_docs':
            return googleDocUrl.value.trim().length > 0
        case 'google_sheets':
            return googleSheetsUrl.value.trim().length > 0
        default:
            return false
    }
})

const dynamicSources = computed(() => {
    return proxySources.value.filter(source => isDynamicSource(source.source_type))
})


// Methods
const isDynamicSource = (sourceType: string): boolean => {
    return ['url_import', 'google_docs', 'google_sheets'].includes(sourceType)
}

const refreshDynamicSource = async (sourceId: string) => {
    refreshingSource.value = sourceId
    try {
        // Здесь можно добавить API вызов для обновления динамического источника
        // await api.refreshStrategyProxySource(props.strategyId, sourceId)
        console.log('Refreshing dynamic source:', sourceId)

        // Перезагружаем статистику
        await loadProxyStats()
    } catch (error) {
        console.error('Error refreshing dynamic source:', error)
    } finally {
        refreshingSource.value = null
    }
}

const truncateUrl = (url: string): string => {
    if (url.length <= 50) return url
    return url.substring(0, 47) + '...'
}

const refreshDynamicProxies = async () => {
    loadingDynamic.value = true
    try {
        await loadProxyStats()

        // Обновляем превью для всех развернутых источников
        for (const sourceId of expandedSources.value) {
            await refreshSourcePreview(sourceId)
        }
    } catch (error) {
        console.error('Error refreshing dynamic proxies:', error)
    } finally {
        loadingDynamic.value = false
    }
}

const refreshSourcePreview = async (sourceId: string) => {
    refreshingPreview.value = sourceId
    try {
        const response = await api.getStrategyProxySourcePreview(props.strategyId, sourceId)

        if (response.data.success) {
            sourcePreviewData.value[sourceId] = response.data.proxies
        } else {
            console.error('Preview error:', response.data.error)
            // Показать ошибку пользователю
            sourcePreviewData.value[sourceId] = []
        }

    } catch (error) {
        console.error('Error refreshing source preview:', error)
        sourcePreviewData.value[sourceId] = []
    } finally {
        refreshingPreview.value = null
    }
}

const toggleSourcePreview = (sourceId: string) => {
    const index = expandedSources.value.indexOf(sourceId)
    if (index > -1) {
        expandedSources.value.splice(index, 1)
    } else {
        expandedSources.value.push(sourceId)
        // Автоматически загружаем превью при разворачивании
        if (!sourcePreviewData.value[sourceId]) {
            refreshSourcePreview(sourceId)
        }
    }
}


const handleFileSelect = (event: Event) => {
    const target = event.target as HTMLInputElement
    selectedFile.value = target.files?.[0] || null
}

const importProxies = async () => {
    if (!canImport.value) return

    loading.value = true
    importResult.value = null

    try {
        let result: any

        switch (selectedImportType.value) {
            case 'manual_list':
                result = await api.importStrategyProxiesManual(props.strategyId, manualProxyText.value)
                break

            case 'file_upload':
                if (!selectedFile.value) return
                result = await api.importStrategyProxiesFile(props.strategyId, selectedFile.value)
                break

            case 'url_import':
                result = await api.importStrategyProxiesUrl(props.strategyId, importUrl.value)
                break

            case 'google_docs':
                result = await api.importStrategyProxiesGoogleDoc(props.strategyId, googleDocUrl.value)
                break

            case 'google_sheets':
                result = await api.importStrategyProxiesGoogleSheets(props.strategyId, googleSheetsUrl.value)
                break

            default:
                throw new Error('Неподдерживаемый тип импорта')
        }

        importResult.value = result.data

        if (result.data.success) {
            // Очищаем форму
            resetImportForm()
            // Перезагружаем данные
            await Promise.all([
                loadProxies(),
                loadProxyStats(),
                loadProxySources()
            ])
        }

    } catch (error) {
        console.error('Error importing proxies:', error)
        importResult.value = {
            success: false,
            errors: ['Ошибка при импорте прокси']
        }
    } finally {
        loading.value = false
    }
}

const resetImportForm = () => {
    manualProxyText.value = ''
    importUrl.value = ''
    googleDocUrl.value = ''
    googleSheetsUrl.value = ''
    selectedFile.value = null
    if (fileInput.value) {
        fileInput.value.value = ''
    }
}

const loadProxies = async () => {
    try {
        const data = await strategiesStore.getStrategyProxies(props.strategyId)
        proxies.value = data
    } catch (error) {
        console.error('Error loading proxies:', error)
    }
}

const loadProxyStats = async () => {
    try {
        const data = await strategiesStore.getStrategyProxyStats(props.strategyId)
        stats.value = data
    } catch (error) {
        console.error('Error loading proxy stats:', error)
    }
}

const loadProxySources = async () => {
    try {
        const data = await strategiesStore.getStrategyProxySources(props.strategyId)
        proxySources.value = data
    } catch (error) {
        console.error('Error loading proxy sources:', error)
    }
}

const updateProxySettings = async () => {
    try {
        await strategiesStore.updateStrategyProxySettings(props.strategyId, proxySettings.value)
        console.log('Proxy settings updated successfully')
    } catch (error) {
        console.error('Error updating proxy settings:', error)
    }
}

const testProxy = async (proxy: ProxyItem) => {
    try {
        await strategiesStore.testStrategyProxy(props.strategyId, proxy.id)
        console.log('Proxy test completed')
    } catch (error) {
        console.error('Error testing proxy:', error)
    }
}

const deleteProxySource = async (sourceId: string) => {
    if (!confirm('Удалить источник прокси?')) return

    try {
        await strategiesStore.deleteStrategyProxySource(props.strategyId, sourceId)
        await Promise.all([
            loadProxySources(),
            loadProxies(),
            loadProxyStats()
        ])
        console.log('Proxy source deleted successfully')
    } catch (error) {
        console.error('Error deleting proxy source:', error)
    }
}

const getSourceTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
        'manual_list': 'Ручной ввод',
        'file_upload': 'Файл',
        'url_import': 'URL импорт',
        'google_sheets': 'Google Таблицы',
        'google_docs': 'Google Документы'
    }
    return labels[type] || type
}

const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
        case 'url_import':
            return LinkIcon
        case 'google_docs':
            return DocumentIcon
        case 'google_sheets':
            return TableCellsIcon
        default:
            return DocumentTextIcon
    }
}

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU')
}

const fileInput = ref<HTMLInputElement>()

// Lifecycle
onMounted(() => {
    loadProxies()
    loadProxyStats()
    loadProxySources()
})

// Watchers
watch(() => props.strategyId, () => {
    loadProxies()
    loadProxyStats()
    loadProxySources()
})

watch([proxies, dynamicSources], ([staticProxies, dynamicSrcs]) => {
    if (staticProxies.length === 0 && dynamicSrcs.length > 0) {
        showMode.value = 'dynamic'
    }
}, {immediate: true})

// Сброс результата импорта при смене типа
watch(selectedImportType, () => {
    importResult.value = null
})
</script>
