-- Migration 015: Locais de entrega por cliente

CREATE TABLE IF NOT EXISTS local_entrega (
    id          SERIAL PRIMARY KEY,
    cliente     TEXT NOT NULL,
    nome_local  TEXT NOT NULL,
    endereco    TEXT,
    lat         NUMERIC(10, 7),
    lng         NUMERIC(10, 7),
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE pedido_cliente
    ADD COLUMN IF NOT EXISTS local_entrega_id INTEGER REFERENCES local_entrega(id) ON DELETE SET NULL;
