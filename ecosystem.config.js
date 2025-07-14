// ecosystem.config.js
module.exports = {
    apps: [
        {
            name: 'yandex-parser-api',
            script: 'run_api.py',
            interpreter: 'python3',
            cwd: '/var/www/topflight/backend',

            // Environment variables
            env: {
                PYTHONPATH: '/var/www/topflight/backend',
                NODE_ENV: 'development'
            },

            env_production: {
                PYTHONPATH: '/var/www/topflight/backend',
                NODE_ENV: 'production'
            },

            // Logging configuration
            log_file: '/var/www/topflight/logs/backend-api.log',
            out_file: '/var/www/topflight/logs/backend-api-out.log',
            error_file: '/var/www/topflight/logs/backend-api-error.log',
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

            // Process management
            instances: 1,
            autorestart: true,
            watch: false, // Отключаем в продакшене, включаем в разработке
            max_memory_restart: '1G',

            // Graceful restart/shutdown
            kill_timeout: 5000,
            wait_ready: true,
            listen_timeout: 10000,

            // Advanced settings
            node_args: [],
            args: [],

            // Monitoring
            monitoring: false,

            // Development specific settings
            ignore_watch: [
                'node_modules',
                'logs',
                '__pycache__',
                '*.pyc',
                '.pytest_cache',
                'alembic/versions'
            ],

            // Restart policy
            restart_delay: 4000,
            max_restarts: 10,
            min_uptime: '10s'
        },

        // Дополнительный процесс для Celery Worker (если будет нужен)
        {
            name: 'yandex-parser-worker',
            script: 'run_worker.py',
            interpreter: 'python3',
            cwd: '/var/www/topflight/backend',

            env: {
                PYTHONPATH: '/var/www/topflight/backend',
                CELERY_WORKER: 'true'
            },

            log_file: '/var/www/topflight/logs/backend-worker.log',
            out_file: '/var/www/topflight/logs/backend-worker-out.log',
            error_file: '/var/www/topflight/logs/backend-worker-error.log',
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '512M',

            // Этот процесс запускается только при необходимости
            autostart: false
        },

        // Процесс для мониторинга системы (опционально)
        {
            name: 'yandex-parser-monitor',
            script: 'run_monitor.py',
            interpreter: 'python3',
            cwd: '/var/www/topflight/backend',

            env: {
                PYTHONPATH: '/var/www/topflight/backend',
                MONITOR_MODE: 'true'
            },

            log_file: '/var/www/topflight/logs/backend-monitor.log',
            out_file: '/var/www/topflight/logs/backend-monitor-out.log',
            error_file: '/var/www/topflight/logs/backend-monitor-error.log',
            log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

            instances: 1,
            autorestart: true,
            watch: false,
            max_memory_restart: '256M',

            // Запускается каждые 5 минут для мониторинга
            cron_restart: '*/5 * * * *',
            autostart: false
        }
    ]
}
