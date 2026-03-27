
# FactoryOps — Venttos

Sistema **fullstack Flask (MVC)** de gestão industrial para manufatura SMT, cobrindo planejamento de produção, engenharia de processos, controle de qualidade, logística e suporte operacional.

> 🇧🇷 Este README é a referência principal do projeto.

---

## Módulos

| Módulo | Descrição |
|---|---|
| **SMT / Engenharia** | Cadastro de modelos, estudos de tempo, cálculos de UPH/UPD/Takt Time, balanceamento de linha |
| **PCP** | Controle de OPs, apontamento de produção, planejamento de turno (plano de voo), importação de dados coletados |
| **Produção** | Checklist de verificação de linha, medição de pasta de solda, limpeza de stencil |
| **Logística** | Gestão de pedidos, entregas, equipe de entrega e rastreamento por GPS |
| **Configurações** | Setores e linhas, turnos, paradas e intervalos |
| **Suporte** | Central de conhecimento (FAQ), ouvidoria, chamados especializados |
| **Admin** | Gestão de usuários, aprovações, backup do banco de dados |
| **Auth** | Login local, OAuth (Google / GitHub), perfil, push notifications, PWA |

---

## Infraestrutura (Railway)

Dois ambientes separados por branch, no mesmo repositório:

| Ambiente | Branch | Banco |
|---|---|---|
| Produção | `main` | `banco_prod` |
| Desenvolvimento | `develop` | `banco_test` |

**Fluxo de deploy:**
1. Trabalhar e validar em `develop`
2. Abrir Pull Request para `main`
3. Produção atualiza automaticamente após merge

---

## Arquitetura (MVC + Services / Repositories)

```
Controllers (routes/)   →  recebem a requisição, orquestram resposta
Services (services/)    →  regras de negócio e cálculos (nunca SQL)
Repositories (repos/)   →  SQL puro via psycopg3
Templates (templates/)  →  Jinja2, sem lógica de negócio
Static (static/)        →  CSS e JS isolados por página
```

---

## Estrutura do Projeto

```
app/
├── __init__.py                       create_app()
├── config.py                         variáveis de ambiente
├── extensions.py                     conexão PostgreSQL (psycopg3)
├── health.py                         healthcheck
│
├── auth/                             autenticação e usuários
│   ├── decorators.py                 @admin_required
│   ├── models.py                     modelo de usuário (Flask-Login)
│   ├── repository.py                 acesso a dados do usuário
│   ├── profile_repository.py         perfil e avatar
│   ├── routes.py                     login, registro, OAuth, perfil
│   └── service.py                    lógica de autenticação
│
├── cli/                              utilitários de linha de comando
│   ├── employees_importer.py         importação de funcionários via Excel
│   ├── employees_code_generator.py   geração de códigos de funcionário
│   └── set_user_password.py          redefinição de senha via CLI
│
├── repositories/
│   ├── apontamento_repository.py
│   ├── backup_repository.py
│   ├── checklist_linha_repository.py
│   ├── checklist_repository.py
│   ├── controle_ops_repository.py
│   ├── employees_repository.py
│   ├── entregas_repository.py
│   ├── limpeza_stencil_repository.py
│   ├── linha_config_repository.py
│   ├── medicao_pasta_repository.py
│   ├── modelos_repository.py
│   ├── parada_config_repository.py
│   ├── planejamento_repository.py
│   ├── powerbi_repository.py
│   ├── producao_coletada_repository.py
│   ├── production_lines_repository.py
│   ├── push_repository.py
│   ├── suporte_repository.py
│   ├── time_studies_repository.py
│   └── turno_config_repository.py
│
├── routes/
│   ├── pages.py                      rotas HTML (~70 rotas)
│   └── api.py                        API REST JSON (~30 endpoints)
│
├── services/
│   ├── apontamento_service.py
│   ├── backup_service.py
│   ├── checklist_linha_service.py
│   ├── checklist_service.py
│   ├── controle_ops_service.py
│   ├── email_service.py              SendGrid
│   ├── employees_service.py
│   ├── entregas_service.py
│   ├── limpeza_stencil_service.py
│   ├── linha_config_service.py
│   ├── medicao_pasta_service.py
│   ├── modelos_service.py
│   ├── notification_service.py       Web Push (VAPID)
│   ├── parada_config_service.py
│   ├── planejamento_service.py
│   ├── powerbi_service.py
│   ├── producao_coletada_service.py
│   ├── production_lines_service.py
│   ├── time_studies_service.py
│   └── turno_config_service.py
│
├── templates/
│   ├── layouts/                      app.html, app_print.html, auth.html
│   ├── admin/                        backups, chamados de suporte
│   ├── auth/                         login, registro, perfil, usuários
│   ├── config/                       linhas, turnos, paradas
│   ├── engenharia/                   estudo de tempo, folha de cronometragem
│   ├── funcionalidades/              modelos SMT, cadastro, calculadora
│   ├── legal/                        política de privacidade, cookies
│   ├── logistica/                    resumo, rastreamento
│   ├── pcp/                          OPs, apontamento, planejamento, entregas
│   ├── producao/                     checklist, pasta de solda, stencil
│   └── suporte/                      FAQ, ouvidoria, chamados
│
└── static/
    ├── css/
    ├── js/
    ├── images/
    ├── manifest.webmanifest
    └── sw.js                         Service Worker (PWA)
```

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, Flask 3.0.3 |
| Banco de dados | PostgreSQL, psycopg3, Flask-SQLAlchemy |
| Autenticação | Flask-Login, Authlib (OAuth 2.0) |
| Migrations | Flask-Migrate (Alembic) |
| Frontend | Jinja2, Bootstrap 5, JavaScript Vanilla |
| PWA | Service Worker, Web Manifest |
| Email | SendGrid |
| Push Notifications | pywebpush (VAPID) |
| Armazenamento | Cloudinary (avatares) |
| Importação de dados | Pandas, OpenPyXL |
| Servidor | Gunicorn |
| CI | GitHub Actions |
| Hospedagem | Railway |

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz (nunca versionar):

```env
# App
ENVIRONMENT=development
SECRET_KEY=change-me
BASE_URL=http://127.0.0.1:5000

# Banco
DATABASE_URL=postgresql://user:password@host:port/database

# OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Email (SendGrid)
SENDGRID_API_KEY=
SENDGRID_FROM=

# SMTP (alternativo ao SendGrid)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_FROM=

# Push Notifications (VAPID)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIMS_EMAIL=

# Cloudinary (avatares)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

Em Railway, configure essas variáveis no painel do service — não use `.env` em produção.

---

## Rodando Localmente

**1. Clonar**

```bash
git clone https://github.com/eduardoliboriox/factoryops-venttos-prod.git
cd factoryops-venttos-prod
```

**2. Ambiente virtual**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

**3. Dependências**

```bash
pip install -r requirements.txt
```

**4. Executar**

```bash
python run.py
```

Acesse: `http://127.0.0.1:5000`

---

## Principais Rotas

### Páginas

| Rota | Descrição |
|---|---|
| `/` | Início |
| `/dashboard` | Dashboard com KPIs |
| `/powerbi` | Relatórios Power BI |
| `/smt/modelos` | Catálogo de modelos SMT |
| `/smt/cadastro` | Cadastro de modelo |
| `/smt/calcular` | Calculadora SMT |
| `/engenharia/estudo-tempo` | Estudos de tempo |
| `/pcp/controle-ops` | Controle de ordens de produção |
| `/pcp/apontamento` | Apontamento de produção |
| `/pcp/planejamento` | Planejamento de turno |
| `/pcp/planejamento/plano-de-voo` | Plano de voo |
| `/pcp/producao-coletada` | Produção coletada (importação) |
| `/pcp/entregas` | Pedidos e entregas |
| `/logistica` | Resumo logístico |
| `/producao/checklist-verificacao-linha` | Checklist de linha |
| `/producao/medicao-pasta-solda` | Medição de pasta de solda |
| `/producao/limpeza-stencil` | Limpeza de stencil |
| `/config/linhas` | Configuração de linhas |
| `/config/turnos` | Configuração de turnos |
| `/config/paradas` | Configuração de paradas |
| `/suporte/centro-conhecimento` | Central de conhecimento (FAQ) |
| `/suporte/ouvidoria` | Ouvidoria |
| `/admin/backup` | Backup do banco |
| `/auth/admin/users` | Aprovação de usuários |

### API (JSON)

| Endpoint | Descrição |
|---|---|
| `GET/POST/PUT/DELETE /api/modelos` | CRUD de modelos |
| `POST /api/smt/calcular_meta` | Meta/hora a partir do tempo de montagem |
| `POST /api/smt/calcular_tempo` | Tempo inverso a partir da meta/hora |
| `POST /api/calcular_perda` | Perda de produção |
| `GET/POST /api/time-studies` | Estudos de tempo |
| `POST /api/time-studies/<id>/operations` | Adicionar operação |
| `GET /api/production/sectors` | Listar setores |
| `GET /api/production/lines` | Listar linhas por setor |
| `POST /api/push/subscribe` | Inscrição em push notifications |

---

## CI / Healthcheck

O CI executa via GitHub Actions (`.github/workflows/ci.yml`):

- `python -m app.health` — verifica conexão com o banco e configuração
- `pytest` — suíte de testes

---

## Banco de Dados — acesso via psql (Windows)

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" "%DATABASE_URL%"
```

Configure `DATABASE_URL` no ambiente com a string do Railway antes de executar.

---

## Autor

**Eduardo Libório**
`eduardosoleno@protonmail.com`

---

## Licença

Projeto de uso privado/interno.
