CREATE TABLE IF NOT EXISTS turno_config (
    id          SERIAL PRIMARY KEY,
    turno       VARCHAR(20) NOT NULL,
    hora_inicio TIME        NOT NULL,
    hora_fim    TIME        NOT NULL,
    ordem       INT         NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS linha_config (
    id    SERIAL PRIMARY KEY,
    setor VARCHAR(50) NOT NULL,
    linha VARCHAR(50) NOT NULL,
    UNIQUE (setor, linha)
);

CREATE TABLE IF NOT EXISTS controle_ops (
    id                SERIAL PRIMARY KEY,
    filial            VARCHAR(20)  NOT NULL,
    numero_op         VARCHAR(30)  NOT NULL,
    produto           VARCHAR(100) NOT NULL,
    descricao         TEXT,
    armazem           VARCHAR(20),
    setor             VARCHAR(50),
    fase_modelo       VARCHAR(10),
    quantidade        INT          NOT NULL DEFAULT 0,
    produzido         INT          NOT NULL DEFAULT 0,
    pedido_venda      VARCHAR(30),
    item_pedido_venda VARCHAR(10),
    criado_em         TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS apontamento (
    id         SERIAL PRIMARY KEY,
    op_id      INT         NOT NULL REFERENCES controle_ops(id),
    data       DATE        NOT NULL,
    turno      VARCHAR(20) NOT NULL,
    modelo     VARCHAR(100) NOT NULL,
    linha      VARCHAR(50) NOT NULL,
    quantidade INT         NOT NULL DEFAULT 0,
    fase       VARCHAR(10),
    lote       VARCHAR(50),
    criado_em  TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_apontamento_grupo
    ON apontamento (data, turno, modelo, linha, COALESCE(fase, ''));

CREATE TABLE IF NOT EXISTS parada_config (
    id          SERIAL PRIMARY KEY,
    setor       VARCHAR(50),
    linha       VARCHAR(50),
    tipo        VARCHAR(30)  NOT NULL,
    nome        VARCHAR(100) NOT NULL,
    hora_inicio TIME,
    duracao_min INT          NOT NULL DEFAULT 0,
    criado_em   TIMESTAMPTZ  DEFAULT NOW()
);
