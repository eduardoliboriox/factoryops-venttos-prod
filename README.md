
# SMT Manager (Venttos) — Modelos, Estudos de Tempo e Cálculos SMT

Aplicação **Fullstack Flask** (MVC) para gestão de **produção SMT** (Surface Mount Technology), com:
- **Cadastro e gestão de modelos** (código, cliente, setor, linha, fase, meta/hora, tempo de montagem, blank)
- **Estudos de tempo** (ciclo por operação, UPH teórico/real, UPD, balanceamento de linha, Takt Time)
- **Cálculos SMT** (meta/hora, tempo inverso, perda de produção, cálculo rápido)
- **Linhas de produção** (setores e linhas cadastradas)
- **Dashboard e KPIs** (absenteísmo, linhas ativas)
- **Push notifications** (VAPID) e **PWA** (offline + manifest + service worker)
- **Autenticação local + OAuth** (Google / GitHub)

> 🇧🇷 Este README é a referência principal.

---

## ☁️ Infraestrutura (Railway)

Este projeto roda em **Railway + PostgreSQL** e possui **dois ambientes** separados por branch:

### ✅ Produção
- **Service:** `smt-manager-venttos-prod`
- **Branch:** `main`
- **DB:** `banco_prod`
- **Domínio:** *(configurado no Railway)*

### ✅ Desenvolvimento
- **Service:** `smt-manager-venttos-develop`
- **Branch:** `develop`
- **DB:** `banco_test` *(clone do prod)*
- **Domínio:** *(sem domínio)*

### Deploy seguro (fluxo recomendado)
1. Trabalhar e validar na branch `develop`
2. Se estiver estável, abrir Pull Request para `main`
3. Produção nunca quebra durante uso

---

## 🧱 Arquitetura e Organização (MVC + Services/Repositories)

Estrutura pensada para separar responsabilidades:

- **Routes**
  - `app/routes/pages.py` → páginas HTML (Jinja2)
  - `app/routes/api.py` → API REST (JSON)
- **Services** (`app/services/`)
  - Regras de negócio, cálculos SMT, validações, notificações
- **Repositories** (`app/repositories/`)
  - Acesso ao PostgreSQL via SQL puro (psycopg3)
- **Templates/Static**
  - Jinja2 + Bootstrap + JS Vanilla (UI responsiva e mobile-first)

---

## 🗂 Estrutura do Projeto (resumo)

```
├─ .github/
│   └─ workflows/
│         └─ ci.yml
│
├─ app/
│   ├─ __init__.py            # create_app()
│   ├─ config.py              # Configurações / env
│   ├─ extensions.py          # DB (psycopg3)
│   ├─ health.py
│   │
│   ├─ auth/
│   │   ├─ __init__.py
│   │   ├─ decorators.py
│   │   ├─ models.py
│   │   ├─ profile_repository.py
│   │   ├─ repository.py
│   │   ├─ routes.py
│   │   └─ service.py
│   │
│   ├─ cli/
│   │   ├─ __init__.py
│   │   ├─ employees_code_generator.py
│   │   └─ employees_importer.py
│   │
│   ├─ repositories/          # Acesso ao banco (SQL)
│   │   ├─ __init__.py
│   │   ├─ employees_repository.py
│   │   ├─ modelos_repository.py
│   │   ├─ powerbi_repository.py
│   │   ├─ production_lines_repository.py
│   │   ├─ push_repository.py
│   │   └─ time_studies_repository.py
│   │
│   ├─ routes/
│   │   ├─ __init__.py
│   │   ├─ api.py             # Rotas REST (JSON)
│   │   └─ pages.py           # Rotas HTML
│   │
│   ├─ services/              # Regras de negócio
│   │   ├─ __init__.py
│   │   ├─ email_service.py
│   │   ├─ employees_service.py
│   │   ├─ modelos_service.py
│   │   ├─ notification_service.py
│   │   ├─ powerbi_service.py
│   │   ├─ production_lines_service.py
│   │   └─ time_studies_service.py
│   │
│   ├─ templates/             # Jinja2
│   │   ├─ auth/
│   │   │   ├─ mobile/
│   │   │   │    └─ login_choice.html
│   │   │   │    └─ login_form.html
│   │   │   │    └─ register_form.html
│   │   │   │
│   │   │   ├─ forgot_password.html
│   │   │   ├─ login.html
│   │   │   ├─ myperfil.html
│   │   │   ├─ register.html
│   │   │   ├─ reset_password.html
│   │   │   ├─ users_admin.html
│   │   │   └─ users_all.html
│   │   │
│   │   ├─ layouts/
│   │   │   ├─ app.html
│   │   │   ├─ app_print.html
│   │   │   └─ auth.html
│   │   │
│   │   ├─ legal/
│   │   │   ├─ cookies.html
│   │   │   └─ privacy.html
│   │   │
│   │   ├─ cadastro.html
│   │   ├─ calcular.html
│   │   ├─ dashboard.html
│   │   ├─ estudo_tempo.html
│   │   ├─ estudo_tempo_print.html
│   │   ├─ inicio.html
│   │   ├─ mais.html
│   │   ├─ modelos.html
│   │   ├─ offline.html
│   │   └─ powerbi.html
│   │
│   ├─ static/
│   │   ├─ css/
│   │   │   ├─ auth.css
│   │   │   ├─ document-fit.css
│   │   │   ├─ legal.css
│   │   │   ├─ modelos.css
│   │   │   ├─ more.css
│   │   │   ├─ powerbi.css
│   │   │   ├─ style.css
│   │   │   └─ time-studies.css
│   │   │
│   │   ├─ js/
│   │   │   ├─ cookie-consent.js
│   │   │   ├─ dashboard-live.js
│   │   │   ├─ document-fit.js
│   │   │   ├─ input-masks.js
│   │   │   ├─ main.js
│   │   │   ├─ pcp.js
│   │   │   ├─ powerbi-live.js
│   │   │   ├─ powerbi.js
│   │   │   ├─ push-notifications.js
│   │   │   ├─ pwa-install.js
│   │   │   ├─ pwa.js
│   │   │   ├─ register.js
│   │   │   ├─ time-studies-help.js
│   │   │   └─ time-studies.js
│   │   │
│   │   ├─ images/
│   │   ├─ fonts/inter.woff2
│   │   │
│   │   ├─ manifest.webmanifest
│   │   └─ sw.js
│   │
│   └─ utils/
│        └─ text.py
│
├─ migrations/                # Alembic (ainda não utilizado)
├─ tests/                     # pytest
│
├─ .env                       # NÃO versionar
├─ .gitignore
├─ LICENSE
├─ Procfile                   # Railway
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ run.py                     # Entrypoint
└─ runtime.txt
```

---

## ⚙️ Tecnologias

* **Python 3.12**
* **Flask**
* **Jinja2**
* **PostgreSQL**
* **psycopg3**
* **Bootstrap 5**
* **JavaScript (Vanilla)**
* **PWA** (Service Worker + Manifest)
* **Pytest** (estrutura pronta)
* **GitHub Actions** (CI)

---

## 🔐 Variáveis de ambiente (obrigatórias)

Crie um `.env` na raiz (NÃO versionar):

```env
# App
ENVIRONMENT=development
SECRET_KEY=change-me
BASE_URL=http://127.0.0.1:5000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/smt_manager

# OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# SMTP (opcional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_FROM=

# SendGrid (opcional)
SENDGRID_API_KEY=
SENDGRID_FROM=

# Push Notifications (opcional)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
```

✅ Em Railway, configure essas variáveis no painel do service (não use `.env` em produção).

---

## ▶️ Rodando Localmente

### 1) Clonar

```bash
git clone https://github.com/eduardoliboriox/smt-manager-venttos-prod.git
cd smt-manager-venttos-prod
```

### 2) Ambiente virtual

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac**

```bash
python -m venv venv
source venv/bin/activate
```

### 3) Dependências

```bash
pip install -r requirements.txt
```

### 4) Executar

```bash
python run.py
```

Acesse:

* `http://127.0.0.1:5000`

---

## 🧪 Healthcheck e CI

### Healthcheck local

O CI executa:

* `python -m app.health`
* `pytest` (se houver testes)

Arquivo:

* `.github/workflows/ci.yml`

---

## 🗃 Banco de Dados (Railway) — Operação via psql (Windows)

📌 **Importante (segurança):** não coloque senhas/URLs completas no README público.
Use o `DATABASE_URL` do Railway e rode assim:

```bash
"C:\Program Files\PostgreSQL\18\bin\psql.exe" "%DATABASE_URL%"
```

### Sugestão prática (2 atalhos no Windows)

**Produção**

```bash
set ENVIRONMENT=production
"C:\Program Files\PostgreSQL\18\bin\psql.exe" "%DATABASE_URL%"
```

**Desenvolvimento**

```bash
set ENVIRONMENT=develop
"C:\Program Files\PostgreSQL\18\bin\psql.exe" "%DATABASE_URL%"
```

> Em Railway: copie o `DATABASE_URL` do service correto (prod/develop) e configure no ambiente.

---

## 🔁 Fluxos principais do sistema

### Modelos SMT

* Listar modelos por setor, linha e fase
* Cadastrar modelo (código, cliente, setor, linha, fase, meta/hora, tempo de montagem, blank)
* Atualizar meta/hora, tempo de montagem ou blank de um modelo
* Excluir modelo
* Histórico de alterações por modelo (audit trail automático)

Arquivos chave:
* `app/services/modelos_service.py`
* `app/repositories/modelos_repository.py`

### Estudo de Tempo

* Criar estudo por produto/linha com metas de UPH e HC
* Adicionar operações com tempo de ciclo e headcount
* Calcular automaticamente: UPH teórico, UPH real (com perda), UPD, Takt Time, target de ciclo
* Balanceamento de linha: identificar gargalos e operações fora do target
* Recomendações de paralelismo por operação
* Impressão formatada do estudo

Arquivos chave:
* `app/services/time_studies_service.py`
* `app/repositories/time_studies_repository.py`

### Cálculos SMT

* **Meta/hora a partir do tempo de montagem**: dado o tempo de ciclo e o blank, calcula UPH teórico e real (com 10% de perda padrão)
* **Tempo inverso**: dado o UPH meta e o blank, calcula o tempo de montagem necessário
* **Perda de produção**: dado meta/hora e produção real, calcula tempo perdido e peças faltantes
* **Cálculo rápido**: dado meta/hora, minutos e blank, calcula placas ou blanks produzidos

Arquivo chave:
* `app/services/modelos_service.py`

### Linhas de Produção

* Listar setores disponíveis
* Listar linhas por setor

---

## 🧩 Endpoints principais (visão rápida)

### Pages (HTML)

* `/` — Início
* `/dashboard` — Dashboard com KPIs
* `/powerbi` — Relatórios Power BI
* `/smt/modelos` — Gestão de modelos
* `/smt/cadastro` — Cadastro de modelo
* `/smt/calcular` — Calculadora SMT
* `/smt/estudo-tempo` — Estudos de tempo
* `/smt/estudo-tempo/print/<id>` — Impressão de estudo
* `/smt/mais` — Módulos extras (mobile)

### API (JSON)

* `GET /api/modelos` — Listar modelos
* `POST /api/modelos` — Cadastrar modelo
* `PUT /api/modelos` — Atualizar modelo
* `DELETE /api/modelos` — Excluir modelo
* `GET /api/modelos/history` — Histórico de alterações
* `POST /api/modelos/calculo_rapido` — Cálculo rápido de produção
* `POST /api/smt/calcular_meta` — Meta/hora a partir do tempo de montagem
* `POST /api/smt/calcular_tempo` — Tempo inverso a partir da meta/hora
* `POST /api/calcular_perda` — Perda de produção
* `GET /api/time-studies` — Listar estudos de tempo
* `POST /api/time-studies` — Criar estudo
* `GET /api/time-studies/<id>` — Detalhe do estudo com cálculos
* `DELETE /api/time-studies/<id>` — Excluir estudo (admin)
* `POST /api/time-studies/<id>/operations` — Adicionar operação
* `PUT /api/time-studies/operations/<id>` — Atualizar operação
* `DELETE /api/time-studies/operations/<id>` — Excluir operação
* `GET /api/production/sectors` — Listar setores
* `GET /api/production/lines` — Listar linhas por setor
* `GET /api/push/vapid-public-key` — Chave pública VAPID
* `POST /api/push/subscribe` — Registrar subscription de push
* `POST /api/push/unsubscribe` — Remover subscription de push

---

## 📱 PWA

Arquivos:

* `app/static/manifest.webmanifest`
* `app/static/sw.js`
* Rotas:
  * `/manifest.webmanifest`
  * `/offline`

---

## 🧭 Convenções do projeto

* **Services**: regras e cálculos (nada de SQL aqui)
* **Repositories**: SQL puro + acesso ao DB
* **Routes**:
  * `pages.py` para HTML
  * `api.py` para JSON
* **CSS/JS**: isolados por página sempre que possível
* **Respostas da API**: padrão `{"sucesso": True/False, ...}`

---

## 👨‍💻 Autor

**Eduardo Libório**
📧 `eduardosoleno@protonmail.com`

---

## 📄 Licença

Projeto de uso privado/interno.
