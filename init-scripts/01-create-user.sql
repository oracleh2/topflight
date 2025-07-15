-- init-scripts/01-create-user.sql
-- Создаем пользователя parser_user с расширенными правами

-- Создаем пользователя с дополнительными привилегиями
CREATE USER parser_user WITH
    PASSWORD 'parser_password'
    CREATEDB
    CREATEROLE
    LOGIN
    SUPERUSER;

-- Альтернативный вариант без SUPERUSER (более безопасный):
-- CREATE USER parser_user WITH
--     PASSWORD 'parser_password'
--     CREATEDB
--     CREATEROLE
--     LOGIN;

-- Даем полные права на базу данных
GRANT ALL PRIVILEGES ON DATABASE yandex_parser TO parser_user;

-- Даем права на схему public
GRANT ALL ON SCHEMA public TO parser_user;
GRANT CREATE ON SCHEMA public TO parser_user;
GRANT USAGE ON SCHEMA public TO parser_user;

-- Даем права владельца на схему
ALTER SCHEMA public OWNER TO parser_user;

-- Даем права на все будущие таблицы и последовательности
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO parser_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO parser_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO parser_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO parser_user;

-- Даем права на системные каталоги (для metadata операций)
GRANT USAGE ON SCHEMA information_schema TO parser_user;
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO parser_user;
GRANT USAGE ON SCHEMA pg_catalog TO parser_user;
GRANT SELECT ON ALL TABLES IN SCHEMA pg_catalog TO parser_user;

-- Даем права на выполнение административных функций
GRANT EXECUTE ON FUNCTION pg_reload_conf() TO parser_user;

-- Если нужно без SUPERUSER, добавляем специфичные права:
-- GRANT CREATE ON DATABASE yandex_parser TO parser_user;
-- GRANT TEMPORARY ON DATABASE yandex_parser TO parser_user;
-- GRANT CONNECT ON DATABASE yandex_parser TO parser_user;

-- Выводим информацию о созданном пользователе
\echo 'User parser_user created successfully with extended privileges'

-- Показываем права пользователя
\echo 'User privileges:'
SELECT rolname,
       rolsuper,
       rolcreatedb,
       rolcreaterole,
       rolcanlogin
FROM pg_roles
WHERE rolname = 'parser_user';
