UPDATE pg_database SET datistemplate = FALSE WHERE datname = 'template1';
DROP DATABASE template1;
CREATE DATABASE template1 WITH TEMPLATE = template0 ENCODING='UNICODE' LC_COLLATE='en_US.UTF8' LC_CTYPE='en_US.UTF8';
UPDATE pg_database SET datistemplate = TRUE WHERE datname = 'template1';
