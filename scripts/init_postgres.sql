SELECT 'CREATE DATABASE honcho_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'honcho_db')\gexec
