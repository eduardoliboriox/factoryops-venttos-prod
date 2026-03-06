## Papel

Atue como engenheiro de software sênior fullstack especializado em Python/Flask, arquitetura MVC, API REST, Clean Code, princípios SOLID e UI/UX responsiva.

---

## Arquitetura

O projeto segue **MVC estritamente**. Toda decisão arquitetural deve respeitar essa estrutura.

| Camada | Responsabilidade |
|---|---|
| Models | Estrutura e mapeamento de dados |
| Repositories | Acesso ao banco (SQL isolado) |
| Services | Regras de negócio |
| Controllers / Routes | Orquestração de request/response |
| Templates | Apresentação (Jinja2, sem lógica) |
| Static | CSS e JS separados do HTML |

**MVP é proibido** em backend, serviços, repositórios e APIs. É permitido exclusivamente na camada de apresentação, quando a separação estrutural prejudicar clareza ou performance, mediante justificativa técnica explícita.

**JS e CSS permanecem em arquivos separados**, exceto em ajustes pontuais de impressão, interações verdadeiramente mínimas e isoladas, ou quando tecnicamente inevitável — neste caso, com justificativa.

---

## Projeto

- Plataforma: Railway
- Banco: PostgreSQL
- 2 serviços independentes no mesmo repositório
- Deploy controlado por branch

| Ambiente | Serviço | Branch | Banco |
|---|---|---|---|
| Produção | smt-manager-venttos-prod | `main` | banco_prod |
| Desenvolvimento | smt-manager-venttos-develop | `develop` | banco_test |

---

## Processo de Trabalho

- Claude Code tem acesso direto aos arquivos — não é necessário colar arquivos no chat
- Ajustes de banco via psql manual
- Não incluir comandos de deploy

---

## Requisitos Técnicos

- Código limpo, sem comentários de nenhum tipo
- Responsabilidades bem definidas por camada
- Nenhuma lógica de negócio em templates
- Queries otimizadas; cache quando aplicável
- Nenhuma alteração fora do escopo da tarefa
- Nenhuma funcionalidade existente removida ou degradada
- Arquivos entregues sempre completos quando alterados

---

## Política de Alteração Arquitetural

Alterações em Services, Controllers, Models, Repositories ou APIs são permitidas **apenas quando necessárias ao objetivo da tarefa**, de forma controlada e com justificativa técnica explícita. A integridade do sistema é inegociável.

---

## Regra de Deployment

- Toda alteração é desenvolvida na branch `develop`
- Nunca alterar `main` diretamente
- A migração para `main` é feita pelo usuário via Pull Request no GitHub após validação

---

## Fluxo de Trabalho com Claude Code

Para cada tarefa:

1. Criar branch no padrão kebab-case em inglês a partir de `develop`
2. Analisar os arquivos necessários diretamente no repositório
3. Implementar as alterações respeitando MVC
4. **Testar antes de commitar** — verificar que nada foi quebrado
5. Commitar com mensagem semântica no padrão `type: description`
6. Só commitar após confirmar que está funcionando
7. O usuário faz o Pull Request e Merge para `main` via Git
