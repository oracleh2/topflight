-- Создаем пользователя parser_user
CREATE USER parser_user WITH PASSWORD 'parser_password';

-- Даем полные права на базу данных
GRANT ALL PRIVILEGES ON DATABASE yandex_parser TO parser_user;

-- Даем права на схему public
GRANT ALL ON SCHEMA public TO parser_user;

-- Позволяем создавать объекты в схеме public
GRANT CREATE ON SCHEMA public TO parser_user;

-- Даем права на создание баз данных (для тестов)
ALTER USER parser_user CREATEDB;

