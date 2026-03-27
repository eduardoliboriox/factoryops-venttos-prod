-- =====================================================
-- Migration 002 — Suporte + Backup
-- Executar no banco de dados via psql antes do deploy
-- =====================================================

-- Configuração de backup agendado
CREATE TABLE IF NOT EXISTS backup_config (
    id               SERIAL PRIMARY KEY,
    database_url     TEXT        NOT NULL,
    frequency        VARCHAR(20) NOT NULL DEFAULT 'daily',
    execution_hour   INTEGER     NOT NULL DEFAULT 2,
    execution_minute INTEGER     NOT NULL DEFAULT 0,
    retention_days   INTEGER     NOT NULL DEFAULT 30,
    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Histórico de execuções de backup
CREATE TABLE IF NOT EXISTS backup_logs (
    id            SERIAL PRIMARY KEY,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status        VARCHAR(10) NOT NULL CHECK (status IN ('success', 'failure')),
    file_path     TEXT,
    size_bytes    BIGINT,
    duration_ms   INTEGER,
    checksum      TEXT,
    error_message TEXT
);

-- Mensagens de ouvidoria
CREATE TABLE IF NOT EXISTS ouvidoria_messages (
    id           SERIAL PRIMARY KEY,
    tipo         VARCHAR(20)  NOT NULL,
    mensagem     TEXT         NOT NULL,
    nome_contato VARCHAR(200),
    user_id      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    status       VARCHAR(20)  NOT NULL DEFAULT 'pending'
);

-- Base de conhecimento (FAQ)
CREATE TABLE IF NOT EXISTS faq_items (
    id         SERIAL PRIMARY KEY,
    pergunta   TEXT        NOT NULL,
    resposta   TEXT        NOT NULL,
    categoria  VARCHAR(50),
    ordem      INTEGER     NOT NULL DEFAULT 0,
    is_active  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chamados de suporte especializado
CREATE TABLE IF NOT EXISTS support_tickets (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assunto    TEXT        NOT NULL,
    status     VARCHAR(20) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Mensagens dos chamados de suporte
CREATE TABLE IF NOT EXISTS support_messages (
    id         SERIAL PRIMARY KEY,
    ticket_id  INTEGER     NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_support BOOLEAN     NOT NULL DEFAULT FALSE,
    mensagem   TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Exemplos de FAQ iniciais (opcional — remova se preferir cadastrar manualmente)
INSERT INTO faq_items (pergunta, resposta, categoria, ordem) VALUES
  ('Como faço login no sistema?',
   'Acesse a página de login e informe seu usuário e senha. Se for seu primeiro acesso, aguarde aprovação do administrador.',
   'Acesso', 1),
  ('Esqueci minha senha. Como recuperar?',
   'Na tela de login, clique em "Esqueceu a senha?" e informe seu e-mail cadastrado. Você receberá um link de redefinição.',
   'Acesso', 2),
  ('Como atualizar meu perfil e foto?',
   'Acesse "Minha Conta" no canto superior direito e edite suas informações. Para foto, clique no avatar e faça o upload.',
   'Perfil', 3),
  ('O que é o Estudo de Tempo?',
   'O Estudo de Tempo (Time Study) é a ferramenta para cronometrar operações de produção, calcular UPH e gerar relatórios de tempo padrão.',
   'Funcionalidades', 4),
  ('Como cadastrar um novo modelo SMT?',
   'Acesse Funcionalidades > Cadastro e preencha o formulário "Novo Modelo" com código, cliente, setor, linha e demais parâmetros.',
   'Funcionalidades', 5)
ON CONFLICT DO NOTHING;
