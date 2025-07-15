-- init-scripts/01-create-user.sql
-- Создаем пользователя parser_user с MD5 паролем
CREATE USER parser_user WITH
    PASSWORD 'parser_password'
    CREATEDB
    LOGIN;

-- Даем полные права на базу данных
GRANT ALL PRIVILEGES ON DATABASE yandex_parser TO parser_user;

-- Даем права на схему public
GRANT ALL ON SCHEMA public TO parser_user;
GRANT CREATE ON SCHEMA public TO parser_user;
GRANT USAGE ON SCHEMA public TO parser_user;

-- Даем права на все будущие таблицы и последовательности
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO parser_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO parser_user;

-- Выводим информацию о созданном пользователе
\echo 'User parser_user created successfully with full privileges'
