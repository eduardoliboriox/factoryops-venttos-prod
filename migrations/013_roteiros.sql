CREATE TABLE IF NOT EXISTS roteiros (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(120) NOT NULL,
    cliente     VARCHAR(100) NOT NULL,
    descricao   TEXT,
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roteiro_etapas (
    id          SERIAL PRIMARY KEY,
    roteiro_id  INT NOT NULL REFERENCES roteiros(id) ON DELETE CASCADE,
    setor       VARCHAR(50) NOT NULL,
    ordem       SMALLINT NOT NULL DEFAULT 1,
    observacao  TEXT,
    UNIQUE (roteiro_id, setor)
);

CREATE TABLE IF NOT EXISTS roteiro_modelos (
    id          SERIAL PRIMARY KEY,
    roteiro_id  INT NOT NULL REFERENCES roteiros(id) ON DELETE CASCADE,
    modelo_codigo VARCHAR(100) NOT NULL,
    UNIQUE (roteiro_id, modelo_codigo)
);

CREATE INDEX IF NOT EXISTS idx_roteiros_cliente       ON roteiros(cliente);
CREATE INDEX IF NOT EXISTS idx_roteiro_etapas_rid     ON roteiro_etapas(roteiro_id);
CREATE INDEX IF NOT EXISTS idx_roteiro_modelos_rid    ON roteiro_modelos(roteiro_id);
CREATE INDEX IF NOT EXISTS idx_roteiro_modelos_codigo ON roteiro_modelos(modelo_codigo);
