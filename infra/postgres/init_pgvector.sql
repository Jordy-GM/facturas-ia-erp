CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS proveedores (
    ruc VARCHAR(13) PRIMARY KEY,
    razon_social VARCHAR(300) NOT NULL,
    embedding vector(384)
);
