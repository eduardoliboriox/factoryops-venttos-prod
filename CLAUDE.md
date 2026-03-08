# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role
Act as a senior fullstack software engineer specialized in Python/Flask, MVC architecture, REST API, Clean Code, SOLID principles, and responsive UI/UX.

---

## Architecture
The project strictly follows **MVC**. Every architectural decision must respect this structure.

| Layer | Responsibility |
|---|---|
| Models | Data structure and mapping |
| Repositories | Database access (isolated SQL) |
| Services | Business rules |
| Controllers / Routes | Request/response orchestration |
| Templates | Presentation (Jinja2, no logic) |
| Static | CSS and JS separate from HTML |

**MVP is forbidden** in backend, services, repositories, and APIs. It is permitted exclusively in the presentation layer, when structural separation harms clarity or performance, with explicit technical justification.

**JS and CSS remain in separate files**, except for minor print adjustments, truly minimal and isolated interactions, or when technically unavoidable — in which case, with justification.

---

## Project
- Platform: Railway
- Database: PostgreSQL
- 2 independent services in the same repository
- Deploy controlled by branch

| Environment | Service | Branch | Database |
|---|---|---|---|
| Production | smt-manager-venttos-prod | `main` | banco_prod |
| Development | smt-manager-venttos-develop | `develop` | banco_test |

---

## Work Process
- Claude Code has direct access to files — no need to paste files in the chat
- Database adjustments via manual psql
- Do not include deploy commands

---

## Technical Requirements
- Clean code, no comments of any kind
- Well-defined responsibilities per layer
- No business logic in templates
- Optimized queries; cache when applicable
- No changes outside the scope of the task
- No existing functionality removed or degraded
- Files always delivered complete when modified

---

## Architectural Change Policy
Changes to Services, Controllers, Models, Repositories, or APIs are allowed **only when necessary for the task objective**, in a controlled manner with explicit technical justification. System integrity is non-negotiable.

---

## Deployment Rule
- All changes are developed on the `develop` branch
- Never modify `main` directly
- Migration to `main` is done by the user via Pull Request on GitHub after validation

---

## Workflow with Claude Code

**This workflow is mandatory and must be executed in full for every task, without exception.**

### Step 1 — Sync develop before anything else
```
git checkout develop
git pull origin develop
```
This must be the first action before any code change. No exceptions.

### Step 2 — Create the feature branch
```
git checkout -b type/short-description-in-english
```
Branch must follow kebab-case in English, branched from the updated `develop`.
**No code changes are made before this step is complete.**

### Step 3 — Implement changes
- Analyze the necessary files directly in the repository
- Implement changes respecting MVC
- No changes outside the scope of the task

### Step 4 — Test before committing
Verify that nothing is broken before proceeding. Do not commit broken code.

### Step 5 — Commit
```
git add .
git commit -m "type: short description"
```
Semantic format: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`

### Step 6 — Rebase on develop to prevent conflicts
```
git fetch origin
git rebase origin/develop
```
Resolve any conflicts before pushing. This step prevents conflicts in the Pull Request.

### Step 7 — Push to remote
```
git push origin type/short-description-in-english
```
**Push is mandatory at the end of every task. The task is not complete until the branch is pushed to GitHub.**

### Step 8 — Stop
Do not suggest next steps, improvements, or additional tasks. The task ends after the push.

---

## Conflict Rule
- Always rebase on `origin/develop` before pushing (Step 6)
- Never merge `develop` into the feature branch — always rebase
- Never use `git push --force` without explicit authorization from the user
