-- Migration 010: Entregas e Logística

CREATE TABLE IF NOT EXISTS pedido_cliente (
    id              SERIAL PRIMARY KEY,
    numero_pedido   TEXT NOT NULL,
    cliente         TEXT NOT NULL,
    modelo          TEXT NOT NULL,
    familia         TEXT,
    quantidade      INTEGER NOT NULL DEFAULT 0,
    data_pedido     DATE NOT NULL,
    data_entrega    DATE NOT NULL,
    observacao      TEXT,
    status          TEXT NOT NULL DEFAULT 'aberto',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS equipe_entrega (
    id          SERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    tipo        TEXT NOT NULL CHECK (tipo IN ('motorista', 'apoio')),
    telefone    TEXT,
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS entrega (
    id                  SERIAL PRIMARY KEY,
    pedido_id           INTEGER NOT NULL REFERENCES pedido_cliente(id) ON DELETE CASCADE,
    motorista_id        INTEGER REFERENCES equipe_entrega(id),
    nota_fiscal         TEXT,
    status              TEXT NOT NULL DEFAULT 'aguardando_nf',
    data_saida          TIMESTAMPTZ,
    data_entrega_real   TIMESTAMPTZ,
    lat                 NUMERIC(10, 7),
    lng                 NUMERIC(10, 7),
    localizacao_em      TIMESTAMPTZ,
    observacao          TEXT,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS entrega_equipe (
    entrega_id  INTEGER NOT NULL REFERENCES entrega(id) ON DELETE CASCADE,
    membro_id   INTEGER NOT NULL REFERENCES equipe_entrega(id),
    PRIMARY KEY (entrega_id, membro_id)
);
