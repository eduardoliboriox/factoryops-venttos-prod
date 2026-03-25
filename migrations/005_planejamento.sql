CREATE TABLE IF NOT EXISTS planejamento (
    id                   SERIAL PRIMARY KEY,
    data                 DATE         NOT NULL,
    turno                VARCHAR(20)  NOT NULL,
    setor                VARCHAR(50)  NOT NULL,
    linha                VARCHAR(50)  NOT NULL,
    op_id                INT          REFERENCES controle_ops(id) ON DELETE SET NULL,
    modelo               VARCHAR(100) NOT NULL,
    quantidade_planejada INT          NOT NULL DEFAULT 0,
    taxa_horaria         INT          NOT NULL DEFAULT 0,
    hora_inicio_prevista TIME         NOT NULL,
    hora_fim_prevista    TIME,
    status               VARCHAR(20)  NOT NULL DEFAULT 'PLANEJADO'
                             CHECK (status IN ('PLANEJADO','EM_EXECUCAO','CONCLUIDO','CANCELADO')),
    observacao           TEXT,
    criado_por           VARCHAR(100),
    criado_em            TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_planejamento_data_turno ON planejamento (data, turno);
CREATE INDEX IF NOT EXISTS idx_planejamento_linha      ON planejamento (linha);
CREATE INDEX IF NOT EXISTS idx_planejamento_op_id      ON planejamento (op_id);
