CREATE TABLE IF NOT EXISTS checklist_itens (
    id SERIAL PRIMARY KEY,
    numero INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS checklist_sessoes (
    id SERIAL PRIMARY KEY,
    setor VARCHAR(20) NOT NULL,
    linha VARCHAR(50) NOT NULL,
    modelo VARCHAR(100),
    mes VARCHAR(20),
    responsavel VARCHAR(100),
    user_id INTEGER REFERENCES users(id),
    data_sessao DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS checklist_respostas (
    id SERIAL PRIMARY KEY,
    sessao_id INTEGER REFERENCES checklist_sessoes(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES checklist_itens(id),
    status VARCHAR(5) NOT NULL CHECK (status IN ('ok', 'nok', 'na')),
    observacao TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS checklist_plano_acao (
    id SERIAL PRIMARY KEY,
    sessao_id INTEGER REFERENCES checklist_sessoes(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES checklist_itens(id),
    problema TEXT NOT NULL,
    causa TEXT,
    acao TEXT,
    quando DATE,
    responsavel VARCHAR(100),
    status VARCHAR(20) DEFAULT 'Aberto',
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO checklist_itens (numero, descricao) VALUES
    (1,  'Todos os EPIs necessários estão disponíveis no ambiente de trabalho?'),
    (2,  'Existe identificação adequada dos equipamentos e das docas?'),
    (3,  'O ambiente está limpo e organizado?'),
    (4,  'A iluminação está adequada para o processo?'),
    (5,  'As ferramentas estão identificadas e organizadas?'),
    (6,  'Todos os postos de trabalho possuem instrução de trabalho atualizada?'),
    (7,  'Existe risco ergonômico identificado no posto?'),
    (8,  'O líder e operadores possuem treinamento adequado para a atividade?'),
    (9,  'Os equipamentos estão em condições seguras de uso?'),
    (10, 'O controle de ESD está ativo e em conformidade?'),
    (11, 'Os materiais estão identificados e segregados corretamente?'),
    (12, 'A pasta de solda está dentro do prazo de validade e armazenada corretamente?'),
    (13, 'Os stencils e ferramentas estão limpos e em bom estado de conservação?'),
    (14, 'Os parâmetros das máquinas estão configurados conforme especificação?'),
    (15, 'A documentação de processo está disponível e atualizada no posto?'),
    (16, 'Não há mistura de componentes ou materiais na linha?'),
    (17, 'O fluxo de produção está sendo seguido conforme procedimento?'),
    (18, 'Os dispositivos de medição e controle estão calibrados?'),
    (19, 'Há registro adequado de não conformidades encontradas?'),
    (20, 'O ambiente possui temperatura e umidade dentro dos limites especificados?')
ON CONFLICT DO NOTHING;
